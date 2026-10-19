# Dataset

## Format of `labels.csv`

| Column | Meaning |
|---|---|
| `text` | what was said or shown in the video |
| `category` | `investment_platform`, `pyramid`, `betting`, `giveaway`, `job_offer` or `none` |
| `source` | where the row came from: `real:tiktok`, `real:manual`, `feedback`, or `synthetic:<template>` |
| `lang` | `ru`, `en`, `kk` or `other` |

Every synthetic row starts with `synthetic:` so nobody mistakes it for real data.

## How to collect real examples

1. Find a TikTok video. Do not download or store it. Write down only the text:
   the speech (type it or copy the auto captions) and the text on screen.
2. Remove personal data: names of private people, phone numbers of real people.
3. Pick the category with the table below. If unsure, ask a teammate.
4. Add it:

```bash
python data/tools/add_example.py --text "..." --category betting --source real:tiktok --lang ru
```

| Category | Typical signs |
|---|---|
| investment_platform | % per day, guaranteed profit, crypto bot, "withdraw in 5 minutes" |
| pyramid | pay to join, earn for inviting people, levels, "not a pyramid" |
| betting | fixed matches, sure bets, casino promo codes, free spins |
| giveaway | "you won", pay for delivery, confirm your card |
| job_offer | pay for likes, open a bank card for us, pay for training first |
| none | normal content, including honest bank ads and warnings about scams |

Aim for balance: at least 50 real rows per category, both Russian and English.

## Synthetic data

```bash
python data/tools/generate_synthetic.py --per-offer 5
```

This overwrites `labels.csv` with 800 synthetic rows. Run it only if you have
no real rows yet, or write to another file with `--output`.

## Sample videos

`data/samples/*.mp4` are 11 short videos made by `data/tools/make_sample_videos.py`
(macOS `say` voices, Pillow text, ffmpeg). `samples.csv` lists the expected category.
They are synthetic and only for tests.

## Feedback from users

An admin can download `/api/v1/admin/feedback.csv`. It has the same first four
columns, so you can review rows and append them to `labels.csv`.
