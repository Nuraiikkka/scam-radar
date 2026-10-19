# Testing

## How to run every layer

| Layer | Where | Command |
|---|---|---|
| Backend unit + API + worker + pipeline | `backend/` | `pytest --cov` (needs ffmpeg and Redis; easiest inside Docker, see below) |
| Lint | `backend/` | `ruff check . ../data/tools && ruff format --check . ../data/tools` |
| Flutter unit, widget, contract | `frontend/` | `flutter analyze && flutter test` |
| Flutter in Chrome | `frontend/` | `chromedriver --port=4444 &` then `flutter drive --driver=test_driver/integration_test.dart --target=integration_test/app_test.dart -d web-server --browser-name=chrome --headless` |
| Flutter on Android emulator | `frontend/` | `flutter test integration_test/app_test.dart -d emulator-5554` |
| Browser E2E on the full stack | `e2e/` | `docker compose up -d` in the repo root, then `npx playwright test` |
| Click-through crawler | `e2e/` | `node crawler.mjs` |
| All sample videos through the API | repo root | `python3 backend/scripts/run_samples_live.py` |

Backend tests inside Docker (no local ffmpeg needed). Start the stack first (`docker compose up -d`)
so Redis and the model cache exist, then from the repo root:

```bash
docker build -t scamradar-backend:dev --build-arg REQUIREMENTS=dev.txt backend
```

```bash
docker run --rm --network scamradar_default -v "$PWD:/repo" -v scamradar_models:/models -w /repo/backend -e TEST_REDIS_URL=redis://redis:6379/15 -e TEST_MODEL_CACHE_DIR=/models/cache --entrypoint python scamradar-backend:dev -m pytest
```

## Evidence from the last full run (16 Oct 2026, macOS, Docker Desktop)

- **Backend:** 140 passed (139 + the evaluate script test), coverage 84 %. Slow tests use real
  Whisper `base` and EasyOCR on the sample videos.
- **Flutter:** `flutter analyze` → "No issues found". `flutter test` → 134 passed
  (screen map tests, accessibility at 1.5× text in English and Russian, API client token refresh,
  OpenAPI contract).
- **Flutter in headless Chrome 155:** `flutter drive ... app_test.dart` → "All tests passed."
- **Playwright E2E** on `docker compose up`: 9 of 9 passed, no console errors. Screenshots of every
  step are in `e2e/screenshots/` (01-onboarding … 17-logged-in-again).
- **Crawler:** "clicked 53 controls on 8 screens, problems: 0, dead ends: 0".
- **Contract test catches drift:** renaming one JSON key in `reason.dart` made
  "Reason fields differ" fail; restoring it made all 30 contract checks pass.

### Failure tests on the live stack

| Case | What happened |
|---|---|
| Wrong file type, fake `.mp4`, empty file, 2 MB over the limit, too long | 415 `unsupported_file_type`, 415 `invalid_video`, 422 `empty_file`, 413 `file_too_large`, 422 `video_too_long` (API tests) |
| Removed or private TikTok link | analysis `failed` with `download_failed` / `video_private`; app shows "The check failed" (E2E step 02) |
| Server unreachable | app shows "Cannot reach the server" and an offline banner (HO-06, NAV-05, PR-07) |
| Expired token | refresh and retry; if refresh fails, logged out with a message (NAV-08 tests) |
| Worker stopped | `/health` → `"worker":false`; new analysis stays `queued`; after `docker compose start worker` it finished as `done none 0.16`. After 20 minutes queued it becomes `queue_timeout` (API test) |
| Redis stopped | `/health` → 503; `POST /analyze` → 503 `service_unavailable`; recovered by itself after restart |
| Silent video, video without text | `no_audio`, risk 0.00, reason "no speech or on-screen text was found" |

### Sample videos through the live API

| Video | Lang | Expected | Actual | Risk | Match |
|---|---|---|---|---|---|
| scam_invest_ru | ru | investment_platform | investment_platform | 0.85 | yes |
| scam_invest_en | en | investment_platform | investment_platform | 0.70 | yes |
| scam_betting_ru | ru | betting | betting | 0.59 | yes |
| scam_giveaway_en | en | giveaway | giveaway | 0.63 | yes |
| scam_job_ru | ru | job_offer | job_offer | 0.52 | yes |
| scam_pyramid_en | en | pyramid | pyramid | 0.62 | yes |
| safe_cooking_ru | ru | none | none | 0.11 | yes |
| safe_travel_en | en | none | none | 0.16 | yes |
| safe_warning_ru | ru | none | none | 0.19 | yes |
| silent_scam_screen | ru | investment_platform | investment_platform | 0.84 | yes |
| silent_no_text | – | none | none | 0.00 | yes |

All 11 correct, about 2 s each once models are loaded. These videos are synthetic (see `docs/ML.md`).

## Bugs found by these tests and fixed

1. Scam score was too high on safe text when the model was unsure (fixed: top scam class vs `none`).
2. Reasons listed keywords of other categories (fixed: only reasons that match the verdict).
3. Two API workers created the admin user at the same time and one crashed (fixed and tested).
4. Token refresh could hang forever when the refresh or the retried request failed (fixed, two tests).
5. Share-sheet listener crashed when the native plugin was missing (fixed).
6. Text overflow at phone width: shared-link note, feedback buttons, category picker, statistics legend, risk gauge in Russian at 1.5× text (fixed).
7. History filter chips were 40 px tall, below the 48 px tap target (fixed); desktop web used 40 px buttons (fixed: always 48 px).
8. Browser address bar did not change on pushed screens, so refresh lost the page (fixed).
9. Flutter web focus error after register/login (fixed by switching forms in place and showing the snackbar after the screen closes).
10. Feedback choice was exposed as checkboxes, now radio buttons for screen readers.
11. Rate-limit message said "Too many checks" on the login form (now generic).
12. Statistics chart showed broken fractional axis labels (fixed, test ST-06).
13. Docker: localization files were missing at `pub get`, compose project name ignored the model cache, API start was marked unhealthy too early (all fixed).

## What could not be tested here

See the final report in the pull request and `docs/QA_CHECKLIST.md`: Android emulator and APK build
(no Android SDK on this Mac; CI runs them), iOS build (no CocoaPods), real TikTok downloads,
the share sheet on a physical phone, HTTPS with a real domain, GitHub Actions themselves.
