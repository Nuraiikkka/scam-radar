#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <owner/repo>"
  exit 1
fi
repo="$1"

gh api -X PUT "repos/$repo/branches/main/protection" --input - <<JSON
{
  "required_status_checks": {"strict": true, "contexts": ["backend", "frontend", "android-integration", "e2e"]},
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 1, "require_code_owner_reviews": true},
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

for label in backend ml cv frontend deploy docs bug task; do
  gh label create "$label" --repo "$repo" --force >/dev/null
done

create_issue() {
  gh issue create --repo "$repo" --title "$1" --label "$2" --body "$3" >/dev/null
  echo "created: $1"
}

create_issue "ml: collect 100 real labeled examples" "ml" "Owner: Aisulu. Add real TikTok texts with data/tools/add_example.py using source real:tiktok."
create_issue "ml: retrain and compare with v1.0.0" "ml" "Owner: Aisulu. Run backend/ml/train_text.py and backend/ml/evaluate.py, update docs/ML.md."
create_issue "cv: tune QR and OCR rules on real videos" "cv" "Owner: Aisulu, help: Nuray. Check vision_rules on 20 real videos, add tests for new OCR mistakes."
create_issue "cv: measure OCR speed per frame" "cv" "Owner: Aisulu. Time vision_ocr on the sample videos, try SCAMRADAR_MAX_FRAMES values."
create_issue "cv: add frame de-duplication tests" "cv" "Owner: Aisulu, help: Nuray. Add unit tests for vision_frames.is_similar with real frames."
create_issue "backend: test real TikTok download" "backend" "Owner: Nuray, help: Moldir. Try 10 public TikTok links on the server and record results in docs/TESTING.md."
create_issue "backend: set up daily backups on the VPS" "backend,deploy" "Owner: Nuray, help: Moldir. Follow docs/DEPLOY.md backup section and test a restore."
create_issue "frontend: test the share sheet on a real Android phone" "frontend" "Owner: Adiya. Share a TikTok link to Scam Radar and check the link appears."
create_issue "frontend: build and run on iOS" "frontend" "Owner: Adiya. Follow docs/DEPLOY.md iOS steps on a Mac, record result."
create_issue "docs: rehearse the demo with QA_CHECKLIST" "docs" "Owner: everyone. Go through docs/QA_CHECKLIST.md on a phone and a laptop."
