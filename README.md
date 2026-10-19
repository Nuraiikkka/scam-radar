# Scam Radar

Scam Radar checks a TikTok video for scam signs. You paste a link or upload a
video. The server listens to the speech, reads the text on screen, looks for
QR codes, links and phone numbers, and returns:

- `risk_score` from 0 to 1
- `category`: `investment_platform`, `pyramid`, `betting`, `giveaway`, `job_offer` or `none`
- `reasons`: short explanations, each with its source (speech, screen text, QR, rule)
- evidence: transcript, screen text, links, phone numbers, QR codes

The result is a risk estimate, not a legal verdict.

## Run everything locally (one command)

You need Docker Desktop. From this folder:

```bash
docker compose up --build
```

Open http://localhost:8080. The first start downloads the Whisper and OCR
models (about 250 MB), so the first analysis can take a few minutes.
Admin panel: http://localhost:8080/admin (login `admin@example.com`,
password `admin-password-change-me`, change both in production).

## Folders

| Folder | What is inside |
|---|---|
| `backend/` | API, database, background worker, video analysis |
| `backend/ml/`, `data/` | dataset, text model training and evaluation |
| `frontend/` | Flutter app for Android, iOS and Web |
| `e2e/` | browser tests |
| `deploy/` | Docker, Nginx, Caddy, server scripts |
| `docs/` | guides |

## Documentation

Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Other guides:
[API](docs/API_CONTRACT.md), [database](docs/DATABASE.md), [ML](docs/ML.md),
[deploy](docs/DEPLOY.md), [workflow](docs/WORKFLOW.md),
[testing](docs/TESTING.md), [security](docs/SECURITY.md),
[screens](docs/SCREENS.md), [QA checklist](docs/QA_CHECKLIST.md).

## About the project

Scam videos on TikTok often promise easy money: big daily profits, "sure" bets,
fake prizes or simple jobs for likes. Scam Radar helps people notice these signs
before they send money.

How it works, in short:

1. You give the app a TikTok link or a video file.
2. The server turns the speech into text and reads the text on the screen.
3. It looks for warning signs: promised percentages, Telegram links, phone numbers, QR codes.
4. A small text model guesses the type of scam.
5. You see a risk score from 0 to 100% and a list of reasons.

The result is advice, not proof. The model was trained on example texts made for
testing, so on real videos it can make mistakes. Users can mark a wrong result,
and this feedback helps to improve the model.
