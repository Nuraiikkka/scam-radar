# Гайд для Мольдир: помощь Нурай с бэкендом

## Твоя роль

Главная по бэкенду — Нурай. Ты помогаешь ей: берёшь задачи из issues, пишешь код и тесты,
проверяешь её PR. Ты code owner всех файлов в `backend/` и `deploy/`.

## Где что лежит

- `backend/app/routers/` — эндпоинты API (`analyze.py`, `analyses.py`, `auth.py`, `feedback.py`, `stats.py`, `meta.py`, `admin.py`).
- `backend/app/models.py` — таблицы, `schemas.py` — что принимает и отдаёт API.
- `backend/app/services/downloader.py` — скачивание TikTok, `audio.py` — звук и речь.
- `backend/app/workers/tasks.py` — фоновые задачи: анализ, очистка файлов, heartbeat.
- `backend/tests/` — тесты. `deploy/` — Docker и сервер.

## Запуск

```
docker compose up --build
```

API с примерами запросов: http://localhost:8080/api/v1/docs.
Без Docker (нужны PostgreSQL, Redis, ffmpeg): в `backend` создай `.venv`,
`pip install -r requirements/dev.txt`, скопируй `app/settings/.env.example` в `.env`,
`alembic upgrade head`, `uvicorn app.main:app --reload`, в другом окне
`celery -A app.workers.celery_app worker --beat`.

## Как добавить эндпоинт

1. Схемы запроса и ответа — в `schemas.py`.
2. Функция в нужном файле `routers/`. Ошибки: `raise AppError("code", "текст", 404)`.
3. Тест в `tests/test_api_*.py` через `client.get(...)` / `client.post(...)`.
4. Обнови контракт: `python scripts/export_openapi.py ../frontend/test/contract/openapi.json`.
5. `ruff check .`, `ruff format .`, тесты.

## Тесты (из корня, когда `docker compose up -d` запущен)

```
docker build -t scamradar-backend:dev --build-arg REQUIREMENTS=dev.txt backend
docker run --rm --network scamradar_default -v "$PWD:/repo" -v scamradar_models:/models -w /repo/backend -e TEST_REDIS_URL=redis://redis:6379/15 -e TEST_MODEL_CACHE_DIR=/models/cache --entrypoint python scamradar-backend:dev -m pytest
```

## Первые задачи

- Проверить 10 публичных ссылок TikTok на сервере, записать результат в `docs/TESTING.md`.
- Настроить ежедневные бэкапы на сервере и проверить восстановление (`docs/DEPLOY.md`, раздел 5).

## Работа в команде

- Ветка: `backend/feat-...`. Коммит: `feat(backend): короткое описание`.
- Твои PR проверяет Адия (и Нурай как главная по бэкенду), ты проверяешь PR Айсулу.
