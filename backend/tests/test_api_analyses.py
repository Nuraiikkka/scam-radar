import shutil
from datetime import UTC, datetime, timedelta

from app.models import Analysis, Video
from app.routers import analyze as analyze_router
from app.services import downloader
from app.settings.conf import settings
from tests.conftest import CLIENT_ID, auth_headers, register, sample_path, upload

ANON = {"X-Client-Id": CLIENT_ID}


def fake_download(url, target_dir):
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "download.mp4"
    shutil.copyfile(sample_path("scam_invest_ru.mp4"), path)
    return {"path": path, "duration": 10, "title": "sample"}


def public_dns(host):
    return ["104.18.20.1"]


def test_upload_runs_analysis(client):
    response = upload(client, sample_path("scam_invest_ru.mp4"))
    assert response.status_code == 202, response.text
    analysis_id = response.json()["analysis_id"]
    result = client.get("/api/v1/analyses/" + analysis_id, headers=ANON).json()
    assert result["status"] == "done"
    assert result["stage"] == "finished"
    assert 0 <= result["risk_score"] <= 1
    assert result["category"] in ["investment_platform", "pyramid", "betting", "giveaway", "job_offer", "none"]
    assert result["reasons"]
    assert result["source_type"] == "upload"
    assert result["original_filename"] == "scam_invest_ru.mp4"
    assert result["processing_seconds"] is not None


def test_uploaded_file_is_deleted_after_analysis(client, db):
    response = upload(client, sample_path("safe_travel_en.mp4"))
    analysis = db.get(Analysis, response.json()["analysis_id"])
    assert analysis.video.stored_path is None
    assert analysis.video.file_deleted_at is not None


def test_url_analysis(client, monkeypatch):
    monkeypatch.setattr(downloader, "resolve_host", public_dns)
    monkeypatch.setattr(downloader, "download_video", fake_download)
    response = client.post("/api/v1/analyze", json={"url": "https://www.tiktok.com/@a/video/1"}, headers=ANON)
    assert response.status_code == 202
    result = client.get("/api/v1/analyses/" + response.json()["analysis_id"], headers=ANON).json()
    assert result["status"] == "done"
    assert result["source_url"] == "https://www.tiktok.com/@a/video/1"


def test_private_video_fails_cleanly(client, monkeypatch):
    def private(url, target_dir):
        raise downloader.DownloadError("video_private", "This video is private")

    monkeypatch.setattr(downloader, "resolve_host", public_dns)
    monkeypatch.setattr(downloader, "download_video", private)
    response = client.post("/api/v1/analyze", json={"url": "https://www.tiktok.com/@a/video/2"}, headers=ANON)
    result = client.get("/api/v1/analyses/" + response.json()["analysis_id"], headers=ANON).json()
    assert result["status"] == "failed"
    assert result["error_code"] == "video_private"
    assert result["risk_score"] is None


def test_rejects_non_tiktok_url(client):
    response = client.post("/api/v1/analyze", json={"url": "https://example.com/video.mp4"}, headers=ANON)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_url"


def test_rejects_ssrf_url(client):
    response = client.post("/api/v1/analyze", json={"url": "http://127.0.0.1:6379/"}, headers=ANON)
    assert response.status_code == 422


def test_rejects_bad_json(client):
    response = client.post("/api/v1/analyze", content=b"{not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    response = client.post("/api/v1/analyze", json=["list"])
    assert response.status_code == 422
    response = client.post("/api/v1/analyze", json={"link": "x"})
    assert response.status_code == 422


def test_rejects_wrong_content_type(client):
    response = client.post("/api/v1/analyze", content=b"hello", headers={"Content-Type": "text/plain"})
    assert response.status_code == 415


def test_rejects_wrong_file_type(client, tmp_path):
    text_file = tmp_path / "notes.txt"
    text_file.write_text("hello")
    response = upload(client, text_file, content_type="text/plain")
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_file_type"


def test_rejects_fake_video(client, tmp_path):
    fake = tmp_path / "fake.mp4"
    fake.write_bytes(b"this is not a video at all" * 100)
    response = upload(client, fake)
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "invalid_video"
    assert list((settings.media_dir / "uploads").glob("*")) == []


def test_rejects_empty_file(client, tmp_path):
    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    response = upload(client, empty)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "empty_file"


def test_rejects_huge_file(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    big = tmp_path / "big.mp4"
    big.write_bytes(b"0" * (2 * 1024 * 1024))
    response = upload(client, big)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_rejects_huge_request_by_header(client):
    response = client.post(
        "/api/v1/analyze",
        content=b"x",
        headers={"Content-Type": "application/json", "Content-Length": str(500 * 1024 * 1024)},
    )
    assert response.status_code == 413


def test_rejects_too_long_video(client, monkeypatch):
    monkeypatch.setattr(settings, "max_video_seconds", 2)
    response = upload(client, sample_path("scam_invest_en.mp4"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "video_too_long"


def test_missing_file_field(client):
    response = client.post("/api/v1/analyze", files={"other": ("a.mp4", b"x", "video/mp4")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "missing_file"


def test_anonymous_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_anonymous_per_hour", 1)
    first = client.post("/api/v1/analyze", json={"url": "https://example.com/x"}, headers=ANON)
    assert first.status_code == 422
    second = client.post("/api/v1/analyze", json={"url": "https://example.com/x"}, headers=ANON)
    assert second.status_code == 429


def test_queue_down_returns_503(client, monkeypatch):
    def broken_delay(analysis_id):
        raise ConnectionError("redis is down")

    monkeypatch.setattr(analyze_router.analyze_video, "delay", broken_delay)
    response = upload(client, sample_path("safe_travel_en.mp4"))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "queue_unavailable"


def test_history_is_private(client):
    response = upload(client, sample_path("safe_travel_en.mp4"))
    analysis_id = response.json()["analysis_id"]
    other = client.get("/api/v1/analyses/" + analysis_id, headers={"X-Client-Id": "another-client-99"})
    assert other.status_code == 404
    nobody = client.get("/api/v1/analyses/" + analysis_id)
    assert nobody.status_code == 404
    assert client.get("/api/v1/analyses").json()["total"] == 0


def test_invalid_client_id(client):
    response = client.get("/api/v1/analyses", headers={"X-Client-Id": "bad id!"})
    assert response.status_code == 400


def test_history_filters_and_pagination(client, db):
    tokens = register(client)
    headers = auth_headers(tokens)
    me = client.get("/api/v1/auth/me", headers=headers).json()
    now = datetime.now(UTC)
    for index in range(5):
        video = Video(source_type="url", source_url="https://www.tiktok.com/@a/video/" + str(index))
        db.add(video)
        db.flush()
        category = "none"
        if index % 2 == 0:
            category = "betting"
        db.add(
            Analysis(
                user_id=me["id"],
                video_id=video.id,
                status="done",
                stage="finished",
                risk_score=index / 5,
                category=category,
                reasons=[],
                links=[],
                phones=[],
                qr_codes=[],
                created_at=now - timedelta(days=index),
            )
        )
    db.commit()
    page = client.get("/api/v1/analyses?page=1&page_size=2", headers=headers).json()
    assert page["total"] == 5
    assert len(page["items"]) == 2
    betting = client.get("/api/v1/analyses?category=betting", headers=headers).json()
    assert betting["total"] == 3
    scored = client.get("/api/v1/analyses?min_score=0.3&max_score=0.7", headers=headers).json()
    assert scored["total"] == 2
    recent = client.get(
        "/api/v1/analyses?date_from=" + (now - timedelta(days=1)).date().isoformat(), headers=headers
    ).json()
    assert recent["total"] == 2
    searched = client.get("/api/v1/analyses?q=video/3", headers=headers).json()
    assert searched["total"] == 1
    bad = client.get("/api/v1/analyses?min_score=5", headers=headers)
    assert bad.status_code == 422


def test_delete_analysis(client):
    response = upload(client, sample_path("safe_travel_en.mp4"))
    analysis_id = response.json()["analysis_id"]
    deleted = client.delete("/api/v1/analyses/" + analysis_id, headers=ANON)
    assert deleted.status_code == 204
    assert client.get("/api/v1/analyses/" + analysis_id, headers=ANON).status_code == 404
    assert client.delete("/api/v1/analyses/" + analysis_id, headers=ANON).status_code == 404


def test_feedback_flow(client):
    response = upload(client, sample_path("safe_travel_en.mp4"))
    analysis_id = response.json()["analysis_id"]
    url = "/api/v1/analyses/" + analysis_id + "/feedback"
    wrong = client.post(
        url, json={"is_correct": False, "true_category": "betting", "comment": "it is betting"}, headers=ANON
    )
    assert wrong.status_code == 201
    assert wrong.json()["true_category"] == "betting"
    right = client.post(url, json={"is_correct": True}, headers=ANON)
    assert right.status_code == 201
    result = client.get("/api/v1/analyses/" + analysis_id, headers=ANON).json()
    assert result["feedback"]["is_correct"] is True
    assert result["feedback"]["true_category"] == result["category"]
    bad = client.post(url, json={"is_correct": False, "true_category": "unknown"}, headers=ANON)
    assert bad.status_code == 422


def test_feedback_needs_finished_analysis(client, db):
    video = Video(source_type="url", source_url="https://www.tiktok.com/@a/video/1")
    db.add(video)
    db.flush()
    analysis = Analysis(
        client_id=CLIENT_ID,
        video_id=video.id,
        status="running",
        stage="listening",
        reasons=[],
        links=[],
        phones=[],
        qr_codes=[],
        started_at=datetime.now(UTC),
    )
    db.add(analysis)
    db.commit()
    response = client.post("/api/v1/analyses/" + analysis.id + "/feedback", json={"is_correct": True}, headers=ANON)
    assert response.status_code == 409


def test_stale_queued_analysis_fails(client, db):
    video = Video(source_type="url", source_url="https://www.tiktok.com/@a/video/1")
    db.add(video)
    db.flush()
    analysis = Analysis(
        client_id=CLIENT_ID,
        video_id=video.id,
        status="queued",
        stage="queued",
        reasons=[],
        links=[],
        phones=[],
        qr_codes=[],
        created_at=datetime.now(UTC) - timedelta(hours=2),
    )
    db.add(analysis)
    db.commit()
    result = client.get("/api/v1/analyses/" + analysis.id, headers=ANON).json()
    assert result["status"] == "failed"
    assert result["error_code"] == "queue_timeout"


def test_stale_running_analysis_fails(client, db):
    video = Video(source_type="url", source_url="https://www.tiktok.com/@a/video/1")
    db.add(video)
    db.flush()
    analysis = Analysis(
        client_id=CLIENT_ID,
        video_id=video.id,
        status="running",
        stage="listening",
        reasons=[],
        links=[],
        phones=[],
        qr_codes=[],
        started_at=datetime.now(UTC) - timedelta(hours=2),
    )
    db.add(analysis)
    db.commit()
    result = client.get("/api/v1/analyses/" + analysis.id, headers=ANON).json()
    assert result["error_code"] == "processing_timeout"


def test_login_claims_anonymous_history(client):
    upload(client, sample_path("safe_travel_en.mp4"))
    tokens = register(client, client_id=CLIENT_ID)
    history = client.get("/api/v1/analyses", headers=auth_headers(tokens)).json()
    assert history["total"] == 1
    assert client.get("/api/v1/analyses", headers=ANON).json()["total"] == 0


def test_logged_in_upload_is_tied_to_user(client):
    tokens = register(client)
    response = upload(client, sample_path("safe_travel_en.mp4"), headers=auth_headers(tokens))
    analysis_id = response.json()["analysis_id"]
    assert client.get("/api/v1/analyses/" + analysis_id, headers=auth_headers(tokens)).status_code == 200
    assert client.get("/api/v1/analyses/" + analysis_id, headers=ANON).status_code == 404


def test_stats(client):
    upload(client, sample_path("safe_travel_en.mp4"))
    upload(client, sample_path("scam_invest_ru.mp4"))
    stats = client.get("/api/v1/stats", headers=ANON).json()
    assert stats["total_analyses"] == 2
    assert stats["done_analyses"] == 2
    assert len(stats["per_category"]) == 6
    assert 0 <= stats["scam_share"] <= 1
    assert stats["risk_over_time"][0]["count"] == 2
    empty = client.get("/api/v1/stats").json()
    assert empty["total_analyses"] == 0
    everyone = client.get("/api/v1/stats?scope=all").json()
    assert everyone["total_analyses"] == 2


def test_categories_and_health(client):
    categories = client.get("/api/v1/categories").json()
    assert [item["id"] for item in categories] == [
        "investment_platform",
        "pyramid",
        "betting",
        "giveaway",
        "job_offer",
        "none",
    ]
    health = client.get("/api/v1/health")
    assert health.json()["database"] is True
    assert health.json()["version"] == "1.0.0"


def test_metrics(client):
    client.get("/api/v1/categories")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "scamradar_http_requests_total" in response.text
    assert 'scamradar_analyses{status="done"}' in response.text


def test_admin_feedback_export(client, db):
    response = upload(client, sample_path("scam_invest_ru.mp4"))
    analysis_id = response.json()["analysis_id"]
    analysis = db.get(Analysis, analysis_id)
    analysis.transcript = "Приведи друга и получи бонус"
    db.commit()
    client.post(
        "/api/v1/analyses/" + analysis_id + "/feedback",
        json={"is_correct": False, "true_category": "pyramid"},
        headers=ANON,
    )
    user_tokens = register(client)
    forbidden = client.get("/api/v1/admin/feedback.csv", headers=auth_headers(user_tokens))
    assert forbidden.status_code == 403
    admin = client.post("/api/v1/auth/login", json={"email": settings.admin_email, "password": settings.admin_password})
    export = client.get("/api/v1/admin/feedback.csv", headers=auth_headers(admin.json()))
    assert export.status_code == 200
    lines = export.text.strip().splitlines()
    assert lines[0] == "text,category,source,lang,predicted,is_correct,analysis_id"
    assert len(lines) == 2
    assert lines[1].startswith("Приведи друга и получи бонус,pyramid,feedback,")


def test_sqladmin_login_page(client):
    response = client.get("/admin/login")
    assert response.status_code == 200
    denied = client.get("/admin/", follow_redirects=False)
    assert denied.status_code in (302, 303, 307)


def test_delete_all_analyses(client):
    upload(client, sample_path("safe_travel_en.mp4"))
    upload(client, sample_path("safe_cooking_ru.mp4"))
    other = upload(client, sample_path("safe_travel_en.mp4"), headers={"X-Client-Id": "another-client-99"})
    response = client.delete("/api/v1/analyses", headers=ANON)
    assert response.json() == {"deleted": 2}
    assert client.get("/api/v1/analyses", headers=ANON).json()["total"] == 0
    other_id = other.json()["analysis_id"]
    assert client.get("/api/v1/analyses/" + other_id, headers={"X-Client-Id": "another-client-99"}).status_code == 200
    assert client.delete("/api/v1/analyses").json() == {"deleted": 0}
