from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
CATEGORIES = ["investment_platform", "pyramid", "betting", "giveaway", "job_offer", "none"]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_categories():
    assert len(client.get("/categories").json()) == 6


def test_analyze_needs_input():
    assert client.post("/analyze").status_code == 400


def test_analyze_bad_link():
    r = client.post("/analyze", data={"url": "https://example.com/video"})
    assert r.status_code == 400


def test_analyze_file_and_everything_else():
    r = client.post("/analyze", files={"file": ("a.mp4", b"not a real video", "video/mp4")})
    assert r.status_code == 200
    data = r.json()
    assert 0 <= data["risk_score"] <= 1
    assert data["category"] in CATEGORIES
    assert isinstance(data["reasons"], list)
    assert data["assessment"]["status"] in {"risk_signals_detected", "insufficient_evidence"}
    assert isinstance(data["assessment"]["warnings"], list)

    analysis_id = data["id"]
    assert client.get("/analyses/" + str(analysis_id)).status_code == 200
    assert client.get("/analyses").json()["total"] >= 1

    fb = client.post("/analyses/" + str(analysis_id) + "/feedback", json={"is_correct": True})
    assert fb.status_code == 201
    assert client.get("/stats").json()["total_analyses"] >= 1

    assert client.delete("/analyses/" + str(analysis_id)).status_code == 204
    assert client.get("/analyses/" + str(analysis_id)).status_code == 404
