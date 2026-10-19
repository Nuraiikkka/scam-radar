# Гайд для Нурай: бэкенд (главная), помощь Айсулу с CV, репозиторий

## Твоя зона

- **Бэкенд — ты главная.** Мольдир помогает тебе.
  `backend/app/main.py`, `routers/`, `schemas.py`, `models.py`, `db.py`, `security/`, `workers/`,
  `services/downloader.py` (TikTok через yt-dlp), `services/audio.py` (ffmpeg, речь faster-whisper),
  `alembic/` (миграции), `deploy/` (Docker, сервер).
- **CV — помогаешь Айсулу.** Решения по кадрам, OCR и правилам принимает она.
- **Репозиторий:** `.github/` (CI, CODEOWNERS), `docs/`, `scripts/`.

## Путь одного запроса

1. `POST /api/v1/analyze` (`routers/analyze.py`): лимит запросов, проверка файла или ссылки
   (только TikTok, только публичный IP), записи `videos` и `analyses`, задача в Redis, сразу ответ `analysis_id`.
2. Воркер (`workers/tasks.py`) вызывает `pipeline.run_analysis()` — дальше работает часть Айсулу.
3. Приложение спрашивает `GET /api/v1/analyses/{id}` каждые 2 секунды.

## Запуск

```
docker compose up --build
```

API: http://localhost:8080/api/v1/docs. Админка: http://localhost:8080/admin
(`admin@example.com` / `admin-password-change-me`, только локально).

## Настройки, миграции, ошибки

- Настройки: `app/settings/base.py`, локальные в `env/local.py`, сервер в `env/prod.py`,
  выбор по `SCAMRADAR_ENV`. Все переменные описаны в `app/settings/.env.example`. Секреты только из окружения.
- Миграции: `alembic revision --autogenerate -m "..."`, `alembic upgrade head`, `alembic check`.
- Ошибка всегда `{"error": {"code", "message", "request_id"}}`. Новая: `raise AppError("code", "текст", 422)`.
  Скажи Адии добавить перевод кода в `frontend/lib/widgets/labels.dart`.
- Меняешь `schemas.py` — обнови контракт: `python scripts/export_openapi.py ../frontend/test/contract/openapi.json`.

## Тесты (из корня, когда `docker compose up -d` запущен)

```
docker build -t scamradar-backend:dev --build-arg REQUIREMENTS=dev.txt backend
docker run --rm --network scamradar_default -v "$PWD:/repo" -v scamradar_models:/models -w /repo/backend -e TEST_REDIS_URL=redis://redis:6379/15 -e TEST_MODEL_CACHE_DIR=/models/cache --entrypoint python scamradar-backend:dev -m pytest
```

## Как работать с Мольдир

Раздавай ей задачи из бэкенда через issues: новые эндпоинты с тестами, проверка реальных
ссылок TikTok на сервере, бэкапы. Она code owner бэкенда, поэтому может одобрять твои PR.

## Как помогать Айсулу с CV

- Пиши тесты для её новых правил в `backend/tests/test_vision_rules.py`.
- Прогоняй реальные видео и присылай ей тексты, где OCR ошибся.
- Замеряй скорость: `python ml/evaluate.py` до и после её изменений.

## Репозиторий

```
gh repo create OWNER/scam-radar --private --source . --push
./scripts/setup_github.sh OWNER/scam-radar
```

Замени в `.github/CODEOWNERS` имена на настоящие логины GitHub. Деплой: `docs/DEPLOY.md`.

## Работа в команде

- Коммиты в бэкенд от тебя — ровно `feat(backend)`.
- Твои PR проверяет Айсулу, ты проверяешь PR Адии.
