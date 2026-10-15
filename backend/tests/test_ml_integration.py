from pathlib import Path
import pytest

from app.services import ml_classifier, pipeline
from app.services.vision import VisionResult
from app.settings import settings


def prediction(score=.88, verdict='scam'):
    return {'status':'ok', 'score':score, 'verdict':verdict,
            'threshold':.5, 'model':'test_model', 'experimental':True}


def stub_media(monkeypatch, text):
    monkeypatch.setattr(pipeline.audio, 'transcribe', lambda _: text)
    monkeypatch.setattr(pipeline.vision, 'analyze', lambda _: VisionResult())


def test_ml_handles_missing_model(tmp_path):
    result = ml_classifier.predict('some sufficiently long input to classify safely',
                                   enabled=True, model_path=tmp_path/'missing.joblib')
    assert result['status'] == 'model_missing'
    assert result['score'] is None


def test_ml_does_not_predict_from_empty_text():
    assert ml_classifier.predict('', enabled=True)['status'] == 'insufficient_text'
    assert ml_classifier.predict('long enough text' * 10, enabled=False)['status'] == 'disabled'


def test_corrupt_artifact_returns_error(tmp_path):
    path = tmp_path/'bad.joblib'
    path.write_text('not a model')
    assert ml_classifier.predict('sample text ' * 10, enabled=True, model_path=path)['status'] == 'model_error'


def test_binary_model_does_not_invent_category(monkeypatch):
    stub_media(monkeypatch, 'A description with no known categorical evidence.')
    monkeypatch.setattr(ml_classifier, 'predict', lambda *args: prediction())
    result = pipeline.run('fake.mp4')
    assert result['category'] == 'none'
    assert result['risk_score'] == .88
    assert result['ml_prediction']['verdict'] == 'scam'


def test_negative_model_does_not_erase_rules(monkeypatch):
    stub_media(monkeypatch, 'Earn $700 per day with no effort using voice typing to write content.')
    monkeypatch.setattr(ml_classifier, 'predict', lambda *args: prediction(.1, 'legitimate'))
    result = pipeline.run('fake.mp4')
    assert result['category'] == 'job_offer'
    assert result['risk_score'] >= .7


def test_api_persists_ml_prediction_and_handles_unknown_category(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import SessionLocal
    from app.models import ModelPrediction
    monkeypatch.setattr(settings, 'MOCK', False)
    stub_media(monkeypatch, 'A description with no known categorical evidence.')
    monkeypatch.setattr(ml_classifier, 'predict', lambda *args: prediction())
    client = TestClient(app)
    response = client.post('/analyze', files={'file':('video.mp4',b'fake', 'video/mp4')}, data={'url':'string'})
    assert response.status_code == 200
    body = response.json()
    analysis_id = body['id']
    try:
        assert body['ml_prediction'] == prediction()
        assert body['verdict'] == 'suspected_scam'
        assert body['category'] == 'none'
        assert body['assessment']['status'] == 'risk_signals_detected'
        assert body['assessment']['category_determined'] is False
        assert body['source_url'] is None
        monkeypatch.setattr(ml_classifier, 'predict', lambda *args: prediction(.1, 'legitimate'))
        saved = client.get(f'/analyses/{analysis_id}').json()
        assert saved['ml_prediction'] == prediction()
        assert any(row['id'] == analysis_id and row['ml_prediction'] == prediction()
                   for row in client.get('/analyses').json()['items'])
    finally:
        assert client.delete(f'/analyses/{analysis_id}').status_code == 204
    with SessionLocal() as db:
        assert db.query(ModelPrediction).filter_by(analysis_id=analysis_id).count() == 0


@pytest.mark.skipif(not Path(settings.ML_MODEL_PATH).is_file(), reason='Local model artifact is not distributed in Git')
def test_uploaded_transcript_reaches_real_trained_model(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    text = 'This video explains how people use gift cards and cryptocurrency online. Check the details carefully before you make any payment.'
    expected = ml_classifier.predict(text, enabled=True)
    assert expected['status'] == 'ok'
    monkeypatch.setattr(settings, 'MOCK', False)
    monkeypatch.setattr(settings, 'ML_ENABLED', True)
    stub_media(monkeypatch, text)
    client = TestClient(app)
    # Only speech/OCR are stubbed; actual saved TF-IDF model and DB are used.
    response = client.post('/analyze', files={'file':('video.mp4', b'fake', 'video/mp4')})
    assert response.status_code == 200
    body = response.json()
    try:
        assert body['ml_prediction'] == expected
        assert body['risk_score'] >= round(expected['score'], 4)
        assert client.get(f"/analyses/{body['id']}").json()['ml_prediction'] == expected
    finally:
        client.delete(f"/analyses/{body['id']}")
