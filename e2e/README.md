# Browser end-to-end tests

These tests drive the real web app in Chrome against the full Docker stack.

## Run

```bash
docker compose up -d --build
```

```bash
cd e2e && npm ci && npx playwright install chromium && npx playwright test
```

```bash
node crawler.mjs
```

Set `E2E_CHANNEL=chrome` to use your installed Chrome instead of the Playwright download.
Set `E2E_TIKTOK_URL=https://www.tiktok.com/...` to also check one real TikTok link.
Set `E2E_BASE_URL` to test another server.

## What `tests/full_flow.spec.mjs` does (a screenshot is saved at every step)

| Step | Checks | Screenshots |
|---|---|---|
| 01 | onboarding, skip, accept, home | 01, 02 |
| 02 | empty and wrong link errors; a removed TikTok video fails with a clear message | 03, 04, 05 |
| 03 | upload `scam_invest_ru.mp4`, progress, result "Investment platform", screen text evidence | 06, 07, 08 |
| 04 | feedback "Yes, correct" | 09 |
| 05 | history shows the upload, swipe to delete | 10, 11 |
| 06 | statistics, "Everyone" scope | 12 |
| 07 | Russian language, dark theme | 13, 14 |
| 08 | register, log out, wrong password, log in | 15, 16, 17 |
| 09 | no console errors or failed requests during the whole run | – |

## Crawler

`crawler.mjs` opens every screen (including a real result), clicks every visible
button, tab, checkbox and radio one by one, and fails on any console error,
server error, failed request or a screen with no way out.

## Tips

- Flutter web builds its accessibility tree only when asked (that keeps scrolling fast).
  `enableAccessibility()` clicks Flutter's hidden "Enable accessibility" button after every
  page load, the same way a screen reader does, so `getByRole` works. Use `typeInto()` for text fields.
- Lists are lazy: use `scrollTo()` before clicking items lower on the page.
- The login rate limit is 30 per hour per IP. Restart Redis to reset it while testing.
