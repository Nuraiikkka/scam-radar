# How we work with Git

## Branches

- `main` is protected: no direct pushes, CI must pass, one review needed.
- One branch per task, named by area:
  `backend/feat-rate-limit`, `cv/feat-qr-rules`, `ml/feat-retrain`,
  `frontend/feat-history-search`, `deploy/fix-caddy`, `docs/update-ml`.

## Commits

Conventional commits: `type(area): short text`, for example
`fix(frontend): history list scrolls on small phones`.
Types: `feat, fix, docs, test, chore, refactor, ci, build, perf`.
Areas: `backend, ml, cv, frontend, deploy, docs, data, repo`.

**Rule for Nuray's backend pushes:** the commit message is exactly `feat(backend)`.

## Pull requests

1. Push your branch and open a PR. The template asks how you tested.
2. CI runs: ruff, pytest with coverage, migrations check, `flutter analyze`,
   `flutter test`, web integration tests, Android emulator tests, Playwright
   end-to-end tests, the click crawler and the API contract check.
3. Review circle: **Nuray → Aisulu → Moldir → Adiya → Nuray**
   (Nuray's PRs are reviewed by Aisulu, Aisulu's by Moldir, and so on).
   CODEOWNERS adds the owner of the folder too.
4. Merge with "Squash and merge". Delete the branch.

## One-time GitHub setup (team lead)

```bash
gh repo create OWNER/scam-radar --private --source . --push
```

```bash
./scripts/setup_github.sh OWNER/scam-radar
```

The script protects `main`, creates labels and the first issues. Then edit
`.github/CODEOWNERS` and replace `@nuray-github` and the others with real GitHub names.

## Project board

Create a GitHub Project (Board view) with columns:
**Backlog → This week → In progress → In review → Done**.
Add all issues from the script. Each card has one owner. Move your own cards.
Planning on Monday, short standup notes in `docs/standups.md`, a summary of the
week in `docs/teamwork_log.md` on Friday.
