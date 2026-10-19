# API contract

Base path: `/api/v1`. Interactive docs: `/api/v1/docs`. Full schema:
`/api/v1/openapi.json` (a copy lives in `frontend/test/contract/openapi.json`).

## Endpoints

| Method | Path | Body / query | Answer |
|---|---|---|---|
| POST | `/analyze` | JSON `{"url": "..."}` or multipart `file` | 202 `{analysis_id, status}` |
| GET | `/analyses/{id}` | | analysis with result |
| GET | `/analyses` | `page, page_size, category, status, min_score, max_score, date_from, date_to, q` | `{items, total, page, page_size}` |
| DELETE | `/analyses/{id}` | | 204 |
| DELETE | `/analyses` | | `{deleted}` (all of your finished checks) |
| POST | `/analyses/{id}/feedback` | `{is_correct, true_category?, comment?}` | 201 feedback |
| GET | `/stats` | `scope=mine|all, days` | totals, per category, risk by day |
| GET | `/health` | | `{status, database, redis, worker, version}` |
| GET | `/categories` | | 6 categories with ru/en names |
| POST | `/auth/register`, `/auth/login` | `{email, password}` | `{access_token, refresh_token, token_type, expires_in}` |
| POST | `/auth/refresh` | `{refresh_token}` | new token pair |
| GET | `/auth/me` | | user |
| GET | `/admin/feedback.csv` | admin token | CSV for retraining |

Outside `/api/v1`: `GET /metrics` (Prometheus, internal only), `/admin` (SQLAdmin).

## Who owns an analysis

- Logged in: send `Authorization: Bearer <access_token>`.
- Not logged in: send `X-Client-Id: <random id>` (the app makes one). Your history
  is tied to it. When you log in or register with the same header, your
  anonymous history moves to your account.
- You only see your own analyses. Others get 404.

## Analysis fields

`id, status (queued|running|done|failed), stage, risk_score, category, reasons[],
transcript, transcript_language, ocr_text, links[], phones[], qr_codes[],
source_type (url|upload), source_url, original_filename, model_version,
error_code, error_message, processing_seconds, created_at, finished_at, feedback`.

Each reason: `{source, code, message_en, message_ru}`, where `source` is
`speech`, `screen_text`, `qr`, `rule` or `classifier`.

## Errors

Every error has the same shape:

```json
{"error": {"code": "video_private", "message": "This video is private", "request_id": "..."}}
```

Common codes: `validation_error`, `invalid_url`, `unsupported_file_type`,
`invalid_video`, `file_too_large`, `video_too_long`, `rate_limited`,
`queue_unavailable`, `unauthorized`, `token_expired`, `not_found`.
Failed analyses use: `video_private`, `video_unavailable`, `download_failed`,
`download_timeout`, `queue_timeout`, `processing_timeout`, `internal_error`.

## Changing the API

1. Change `backend/app/schemas.py` and the router.
2. Run `python backend/scripts/export_openapi.py frontend/test/contract/openapi.json`.
3. Update the Dart model in `frontend/lib/data/models/`. The contract test fails until
   field names, types and nullability match exactly.
