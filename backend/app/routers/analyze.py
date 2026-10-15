import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.settings import settings
from app.db import get_db
from app.models import Video, Analysis, Signal, Feedback, ModelPrediction
from app.services import pipeline, downloader, text_classifier

router = APIRouter()
log = logging.getLogger(__name__)


def analysis_to_dict(a):
    reasons = []
    for s in a.signals:
        reasons.append(s.description)

    prediction = a.model_prediction.payload if a.model_prediction else {'status': 'not_recorded'}
    assessment = text_classifier.evidence_summary(a.transcript or "", a.ocr_text or "", a.category)
    ml_scam = prediction.get('status') == 'ok' and prediction.get('verdict') == 'scam'
    verdict = 'suspected_scam' if ml_scam or a.category != 'none' else 'insufficient_evidence'
    if prediction.get('status') == 'ok':
        assessment['warnings'].append('Experimental binary ML score is not a calibrated probability; source labels are partly automated')
        assessment['warnings'].append('ML was trained on a small crypto/giftcard dataset and is not validated for all scam types or languages')
        if ml_scam:
            assessment['status'] = 'risk_signals_detected'
            if a.category == 'none':
                assessment['warnings'] = [w for w in assessment['warnings'] if not w.startswith('No matching fraud evidence')]
                assessment['warnings'].append('ML detected risk but the scam category could not be determined')
    elif prediction.get('status') not in {'disabled', 'mock', 'not_recorded'}:
        assessment['warnings'].append('ML prediction unavailable: ' + prediction.get('status', 'unknown'))
    assessment['category_determined'] = a.category != 'none'

    return {
        "id": a.id,
        "video_id": a.video_id,
        "risk_score": a.risk_score,
        "category": a.category,
        "reasons": reasons,
        "transcript": a.transcript,
        "ocr_text": a.ocr_text,
        "text_score": a.text_score,
        "vision_score": a.vision_score,
        "processing_ms": a.processing_ms,
        "source_url": a.video.source_url,
        "created_at": a.created_at.isoformat(),
        "assessment": assessment,
        "verdict": verdict,
        "ml_prediction": prediction,
    }


@router.post("/analyze")
async def analyze(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if file is not None and file.filename == "":
        file = None

    # Swagger's optional URL placeholder is not the uploaded file's source.
    url = None if file is not None else (url.strip() if url else None)

    if file is None and not url:
        raise HTTPException(status_code=400, detail="Send a video file or a TikTok url")

    video_path = ""
    result = None

    try:
        if settings.MOCK:
            result = pipeline.run_mock()
        else:
            if file is not None:
                data = await file.read()
                if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="File is too large")
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                temp.write(data)
                temp.close()
                video_path = temp.name
            else:
                if "tiktok.com" not in url:
                    raise HTTPException(status_code=400, detail="This is not a TikTok link")
                try:
                    video_path = downloader.download(url)
                except downloader.DownloadError as error:
                    raise HTTPException(status_code=400, detail=str(error))

            result = await run_in_threadpool(pipeline.run, video_path)
    finally:
        if video_path != "" and os.path.exists(video_path):
            os.remove(video_path)

    video = Video(
        source_url=url,
        filename=file.filename if file is not None else None,
        duration_sec=result["duration_sec"],
    )
    db.add(video)
    db.commit()

    analysis = Analysis(
        video_id=video.id,
        risk_score=result["risk_score"],
        category=result["category"],
        transcript=result["transcript"],
        ocr_text=result["ocr_text"],
        text_score=result["text_score"],
        vision_score=result["vision_score"],
        processing_ms=result["processing_ms"],
    )
    db.add(analysis)
    db.commit()

    if 'ml_prediction' in result:
        db.add(ModelPrediction(analysis_id=analysis.id, payload=result['ml_prediction']))

    for s in result["signals"]:
        db.add(Signal(analysis_id=analysis.id, source=s["source"], description=s["description"][:300]))
    db.commit()

    db.refresh(analysis)
    log.info("analysis %s: %s %.2f in %s ms", analysis.id, analysis.category, analysis.risk_score, analysis.processing_ms)
    return analysis_to_dict(analysis)


@router.get("/analyses")
def list_analyses(
    category: Optional[str] = None,
    min_score: float = 0.0,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Analysis).filter(Analysis.risk_score >= min_score)
    if category:
        query = query.filter(Analysis.category == category)

    total = query.count()
    rows = query.order_by(Analysis.id.desc()).offset(offset).limit(limit).all()

    items = []
    for a in rows:
        items.append(analysis_to_dict(a))
    return {"total": total, "items": items}


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    a = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if a is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_to_dict(a)


@router.delete("/analyses/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    a = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if a is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    db.delete(a.video)
    db.commit()


class FeedbackIn(BaseModel):
    is_correct: bool
    true_category: Optional[str] = None
    comment: Optional[str] = None


@router.post("/analyses/{analysis_id}/feedback", status_code=201)
def add_feedback(analysis_id: int, body: FeedbackIn, db: Session = Depends(get_db)):
    a = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if a is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if body.true_category is not None and body.true_category not in settings.CATEGORIES:
        raise HTTPException(status_code=400, detail="Unknown category")

    fb = Feedback(
        analysis_id=analysis_id,
        is_correct=body.is_correct,
        true_category=body.true_category,
        comment=body.comment,
    )
    db.add(fb)
    db.commit()
    return {"id": fb.id, "analysis_id": analysis_id, "is_correct": fb.is_correct}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(Analysis).count()

    by_category = {}
    for category in settings.CATEGORIES:
        by_category[category] = db.query(Analysis).filter(Analysis.category == category).count()

    all_rows = db.query(Analysis).all()
    scams = sum(
        a.category != 'none' or (
            a.model_prediction is not None
            and a.model_prediction.payload.get('status') == 'ok'
            and a.model_prediction.payload.get('verdict') == 'scam'
        ) for a in all_rows
    )
    total_score = 0.0
    for a in all_rows:
        total_score = total_score + a.risk_score
    avg = round(total_score / total, 3) if total > 0 else 0.0

    feedback_total = db.query(Feedback).count()
    feedback_ok = db.query(Feedback).filter(Feedback.is_correct == True).count()
    accuracy = round(feedback_ok / feedback_total, 3) if feedback_total > 0 else None

    return {
        "total_analyses": total,
        "scam_count": scams,
        "avg_risk_score": avg,
        "by_category": by_category,
        "feedback_total": feedback_total,
        "feedback_accuracy": accuracy,
    }
