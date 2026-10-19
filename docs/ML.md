# ML: data, training, metrics, limits

## Data

- File: `data/labels.csv` with columns `text, category, source, lang`.
- 800 rows, **all synthetic** (`source` starts with `synthetic:`). We had no
  real labeled TikTok data yet. Rows are built from hand-written hooks, offers
  and calls to action in Russian (370), English (370) and Kazakh (60).
- How to add data and label it: `data/README.md`.

## Model

`backend/app/services/text_classifier.py` loads `ml/models/text_model_latest.joblib`:
TF-IDF on character 2–5 grams and word 1–2 grams, then Logistic Regression
(class weights balanced). A keyword rule list gives a second score and the
explanation text. If the model file is missing, the rules alone are used.

Scores, in plain words:
- text score = 0.75 × model scam probability + 0.25 × keyword score;
  model scam probability = top scam class ÷ (top scam class + `none`).
- vision score = 1 − product of (1 − weight) over screen and QR cues
  (each cue type counted at most twice).
- risk = weighted average of text and vision scores (weights in settings).
  If one side has no content (no speech and no screen text), the other side is used alone.
- If risk is below `SCAMRADAR_FUSION_NONE_THRESHOLD` (0.35), the category is `none`.

## Train and evaluate (run in `backend/`)

```bash
python ml/train_text.py --version v1.1.0
```

```bash
python ml/evaluate.py
```

`train_text.py` keeps whole templates out of training (group split), so the
test set has phrasings the model never saw. It prints accuracy, per-class
precision/recall/F1, the confusion matrix and 4-fold cross-validation.

## Measured results (model v1.0.0, 16 Oct 2026)

Held-out set: 200 rows from unseen templates. Accuracy 0.805, **macro F1 0.801**.
4-fold group cross-validation macro F1: 0.801, 0.857, 0.883, 0.749 (mean 0.822).

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| investment_platform | 0.68 | 0.80 | 0.74 | 35 |
| pyramid | 0.81 | 0.83 | 0.82 | 30 |
| betting | 0.67 | 0.67 | 0.67 | 30 |
| giveaway | 0.88 | 0.73 | 0.80 | 30 |
| job_offer | 0.88 | 0.86 | 0.87 | 35 |
| none | 0.92 | 0.90 | 0.91 | 40 |

End to end on 11 sample videos (`data/samples`, made by us with text to speech,
also synthetic): 11 of 11 categories correct, scam vs safe 11 of 11.
Full table: `backend/ml/reports/evaluation_latest.md`.

## Limits (please read)

- All numbers come from synthetic data. Real TikTok videos use slang, music,
  fast speech and stylised fonts. **Expect lower accuracy on real videos.**
- The sample videos have clean computer voices and big clear text. Real OCR
  and speech recognition will make more mistakes.
- Investment vs betting is the weakest pair (7 of 35 investment rows were called betting).
- False positives happen: honest bank ads with percentages, real job offers.
  False negatives happen: new scam wording, scams shown only in pictures.
- Kazakh: the system does not crash, but there are only 60 Kazakh rows.
- The verdict is advice, not proof. The app says this on every result.

## Next steps for the team

Collect real examples (`data/tools/add_example.py`), export user feedback
(`/api/v1/admin/feedback.csv`), retrain, and update this page with new numbers.
