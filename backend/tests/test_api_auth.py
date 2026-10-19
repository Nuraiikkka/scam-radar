from datetime import UTC, datetime, timedelta

import jwt

from app.models import User
from app.settings.conf import settings
from tests.conftest import auth_headers, register


def test_register_login_me(client):
    tokens = register(client)
    assert tokens["token_type"] == "bearer"
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens))
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"
    login = client.post("/api/v1/auth/login", json={"email": "USER@example.com", "password": "password-123"})
    assert login.status_code == 200


def test_register_duplicate_email(client):
    register(client)
    again = client.post("/api/v1/auth/register", json={"email": "user@example.com", "password": "password-123"})
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "email_taken"


def test_register_validation(client):
    short = client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "123"})
    assert short.status_code == 422
    assert short.json()["error"]["code"] == "validation_error"
    bad_email = client.post("/api/v1/auth/register", json={"email": "not-an-email", "password": "password-123"})
    assert bad_email.status_code == 422


def test_wrong_password(client):
    register(client)
    response = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong-pass"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"
    unknown = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "wrong-pass"})
    assert unknown.status_code == 401


def test_refresh_token(client):
    tokens = register(client)
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    wrong_type = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert wrong_type.status_code == 401


def test_expired_token(client):
    tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()
    past = datetime.now(UTC) - timedelta(minutes=5)
    expired = jwt.encode({"sub": str(me["id"]), "type": "access", "exp": past}, settings.secret_key, algorithm="HS256")
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + expired})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_expired"


def test_bad_authorization_header(client):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Token abc"})
    assert response.status_code == 401
    forged = jwt.encode({"sub": "1", "type": "access"}, "another-secret-key-that-is-long-enough", algorithm="HS256")
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + forged})
    assert response.json()["error"]["code"] == "invalid_token"


def test_me_requires_login(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_auth_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_auth_per_hour", 3)
    for _ in range(3):
        client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "whatever"})
    response = client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "whatever"})
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"


def test_error_shape_has_request_id(client):
    response = client.get("/api/v1/nothing-here", headers={"X-Request-ID": "abcdef123456"})
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["request_id"] == "abcdef123456"
    assert response.headers["X-Request-ID"] == "abcdef123456"


def test_admin_creation_tolerates_a_parallel_worker(monkeypatch):
    from app import main

    original_hash = main.hash_password

    def hash_while_other_worker_inserts(password):
        other = main.SessionLocal()
        other.add(User(email=settings.admin_email, password_hash=original_hash(password), is_admin=True))
        other.commit()
        other.close()
        return original_hash(password)

    cleanup = main.SessionLocal()
    cleanup.query(User).filter(User.email == settings.admin_email).delete()
    cleanup.commit()
    cleanup.close()
    monkeypatch.setattr(main, "hash_password", hash_while_other_worker_inserts)
    main.ensure_admin_user()
    check = main.SessionLocal()
    admins = check.query(User).filter(User.email == settings.admin_email, User.is_admin.is_(True)).count()
    check.close()
    assert admins == 1
