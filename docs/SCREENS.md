# Screen map

Every row has an ID. The Flutter test with the same ID in its name checks it.
Tests live in `frontend/integration_test/screens/`. `flutter test` runs them headless
(through `test/screens_test.dart`) and `flutter drive` runs the same tests in Chrome
and on an Android emulator (through `integration_test/app_test.dart`).
Browser E2E steps (Playwright, real backend) are listed in `e2e/README.md`.

## Onboarding `/onboarding`

| ID | Control | Action | Result |
|---|---|---|---|
| ON-01 | First start | open app | onboarding page 1 is shown |
| ON-02 | "Next" button | tap | page 2, then page 3 |
| ON-03 | Swipe | swipe left | next page |
| ON-04 | "Skip" button | tap | last page with disclaimer |
| ON-05 | "I understand, start" | tap | `/home`, onboarding is not shown again |

## Bottom navigation (all tab screens)

| ID | Control | Action | Result |
|---|---|---|---|
| NAV-01 | "Check" tab | tap | `/home` |
| NAV-02 | "History" tab | tap | `/history` |
| NAV-03 | "Statistics" tab | tap | `/stats` |
| NAV-04 | "Settings" tab | tap | `/settings` |
| NAV-05 | Offline banner | network lost | red banner "You are offline" |
| NAV-06 | Deep link | open `/result/<id>` directly | result screen opens |
| NAV-07 | Back button | press back on result | returns to previous screen |
| NAV-08 | Session expired | token refresh fails | snackbar "session has expired" |

## Home `/home`

| ID | Control | Action | Result |
|---|---|---|---|
| HO-01 | Link field + "Check link" | empty field, tap | error "Paste a link first" |
| HO-02 | Link field | not a TikTok link | error "This is not a TikTok link" |
| HO-03 | "Check link" | valid link | `/progress/<id>` |
| HO-04 | Link field | press Enter | same as "Check link" |
| HO-05 | "Check link" | server says `video_private` / `rate_limited` | snackbar with clear message |
| HO-06 | "Check link" | server unreachable | snackbar "Cannot reach the server" |
| HO-07 | "Upload a video file" | pick a video | `/progress/<id>` |
| HO-08 | "Upload a video file" | file over 60 MB | snackbar "larger than 60 MB" |
| HO-09 | "Upload a video file" | cancel picker | nothing happens |
| HO-10 | "Log in" in hint card | tap | `/login` |
| HO-11 | Share sheet (Android/iOS) | share a TikTok link to the app | link is filled in, note "Link received" |

## Progress `/progress/<id>`

| ID | Control | Action | Result |
|---|---|---|---|
| PR-01 | Stage text | analysis runs | shows Downloading → Listening → Reading → Scoring |
| PR-02 | Analysis done | automatic | `/result/<id>` replaces progress |
| PR-03 | Analysis failed | automatic | failed view with clear message |
| PR-04 | "Back to start" (failed view) | tap | `/home` |
| PR-05 | "Continue in background" | tap | `/history` |
| PR-06 | Back arrow | tap | previous screen |
| PR-07 | Server unreachable 5 times | automatic | error view with "Try again" |
| PR-08 | "Try again" | tap | polling restarts |
| PR-09 | Unknown id | open `/progress/<bad>` | "not found" error view |

## Result `/result/<id>`

| ID | Control | Action | Result |
|---|---|---|---|
| RE-01 | Gauge, badge, reasons | open | risk %, category, every reason with source |
| RE-02 | Evidence tiles | tap each of 5 | expands transcript, screen text, links, phones, QR |
| RE-03 | "Share" | tap | share sheet; if missing, copied + snackbar |
| RE-04 | "Wrong verdict?" | tap | feedback sheet opens |
| RE-05 | Feedback "Yes, correct" + Send | tap | thanks snackbar, "already rated" note |
| RE-06 | Feedback "No" + category + comment + Send | tap | thanks snackbar |
| RE-07 | Feedback "No" without category | look | Send is disabled |
| RE-08 | "Check another video" | tap | `/home` |
| RE-09 | Back arrow | tap | previous screen or `/home` |
| RE-10 | Loading / error / offline | slow or failing server | spinner, then error view with "Try again" |
| RE-11 | Failed analysis | open | clear error message |
| RE-12 | Language | switch to Russian | reasons are shown in Russian |

## History `/history`

| ID | Control | Action | Result |
|---|---|---|---|
| HI-01 | List | open | items with risk, category, date |
| HI-02 | Empty state | no items | "No checks yet" |
| HI-03 | Search field | type text | filtered list; "Nothing matches" if empty |
| HI-04 | Filter chips (All + 6 categories) | tap | list filtered by category |
| HI-05 | Pull to refresh, refresh icon | drag down or tap icon | list reloads |
| HI-06 | Swipe left on item | swipe | item deleted, snackbar "Deleted" |
| HI-07 | Tap finished item | tap | `/result/<id>` |
| HI-08 | Tap running item | tap | `/progress/<id>` |
| HI-09 | "Load more" | tap | next page appended |
| HI-10 | Error / offline | server down | error view, "Try again" reloads |

## Statistics `/stats`

| ID | Control | Action | Result |
|---|---|---|---|
| ST-01 | Cards and charts | open | totals, scam share, avg time, bar chart, line chart |
| ST-02 | "Mine" / "Everyone" | tap | stats reload for that scope |
| ST-03 | Empty state | no checks | "No statistics yet" |
| ST-04 | Error / offline | server down | error view, "Try again" reloads |
| ST-05 | Pull to refresh, refresh icon | drag down or tap icon | stats reload |
| ST-06 | Only failed checks | open | "Nothing found" instead of an empty chart |

## Settings `/settings`

| ID | Control | Action | Result |
|---|---|---|---|
| SE-01 | Language "Русский" / "English" | tap | whole UI switches language |
| SE-02 | Theme System / Light / Dark | tap | theme changes |
| SE-03 | "Log in or register" | tap | `/login` |
| SE-04 | "Log out" | tap | logged out snackbar, login button is back |
| SE-05 | "Clear history" → "Cancel" | tap | nothing deleted |
| SE-06 | "Clear history" → "Confirm" | tap | history empty, snackbar with count |
| SE-07 | Server URL field + "Save server" | invalid URL | validation error |
| SE-08 | Server URL field + "Save server" | valid URL | snackbar "Server saved", API uses it |
| SE-09 | "Use default" | tap | field resets to default server |
| SE-10 | "Show the introduction again" | tap | `/onboarding` |
| SE-11 | Version text | look | "Version 1.0.0" |

## Login `/login` and Register `/register`

| ID | Control | Action | Result |
|---|---|---|---|
| AU-01 | Email + password, "Log in" | empty / bad email | validation errors |
| AU-02 | "Log in" | correct data | snackbar "You are logged in", goes back |
| AU-03 | "Log in" | wrong password | error "Wrong email or password" |
| AU-04 | Eye icon | tap | password shown / hidden |
| AU-05 | "No account? Register" | tap | form switches to register |
| AU-06 | "Already have an account? Log in" | tap | form switches to log in |
| AU-07 | Register | password < 8 chars | error "At least 8 characters" |
| AU-08 | Register | email taken | error "already exists" |
| AU-09 | Register | valid | logged in, goes back |
| AU-10 | "Continue without an account" / back arrow | tap | previous screen |
| AU-11 | Settings → register → log out → wrong password → log in | full flow | logged in, no errors |

## Accessibility (every screen)

| ID | Check | Result |
|---|---|---|
| A11Y-en / A11Y-ru | every screen at 1.5× text size in English and Russian | no overflow |
| A11Y | tap targets, labels, text contrast on every screen | meets Android and WCAG guidelines |
| A11Y | dark theme | text contrast still passes |
