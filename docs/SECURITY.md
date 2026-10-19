# Security and privacy

## What we protect against

| Risk | What we do |
|---|---|
| Stolen passwords | argon2 hashing, same error for wrong email and wrong password, login rate limit |
| Token theft | short access token (30 min), refresh token (14 days), secret only from env |
| Abuse and cost | rate limits: 10 checks per hour per IP without login, 60 with login, 30 auth attempts per hour |
| SSRF (making our server call internal addresses) | only TikTok hosts allowed, DNS result must be a public IP, yt-dlp limited to TikTok extractors, no user data in URLs |
| Huge or fake files | 60 MB limit in Nginx and the API, extension and type check, ffprobe must read it, 180 s max |
| Shell injection | ffmpeg and ffprobe are called with an argument list, never a shell string |
| Leaking other people's history | every analysis is tied to a user or client id; others get 404 |
| Server details in errors | one JSON error shape, no stack traces, request id for support |
| Browser attacks | CORS from settings, `nosniff`, `X-Frame-Options: DENY`, HTTPS with HSTS |
| Admin panel | needs an admin account; `/metrics` is not public |
| Containers | non-root users, resource limits, secrets only in `deploy/.env` (mode 600) |

## Privacy and TikTok terms

- We store **no video files** after the analysis by default
  (`SCAMRADAR_VIDEO_RETENTION_HOURS=0`). A cleanup task also removes any leftover
  files and temp folders every 30 minutes. If you set retention above 0, files are
  deleted after that many hours.
- We keep the text results (transcript, screen text, links) so users can see their
  history. Users can delete one item or their whole history from the app.
- We store only an email and a password hash for accounts. Anonymous users get a
  random device id, not linked to any personal data.
- We do not re-publish videos and only download a single public video that the user
  asked us to check. Private videos are refused. Do not use the tool for mass scraping;
  this respects TikTok's terms of service.
- Feedback CSV for retraining contains only text, category and language.
- The result is advice, not proof. Do not use it to accuse a person publicly.

## Known limits

- Refresh tokens cannot be revoked one by one; changing `SCAMRADAR_SECRET_KEY`
  logs everyone out.
- Anyone who learns an anonymous client id can see that device's history.
- Logs contain request paths and status codes, not request bodies.

## Report a problem

Write to the team lead (Nuray). Do not open a public issue for security bugs.
