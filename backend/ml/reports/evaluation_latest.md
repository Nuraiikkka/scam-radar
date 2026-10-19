# End-to-end evaluation

Videos: 11

Category accuracy: 1.0

Category macro F1: 1.0

Scam vs safe accuracy: 1.0

| Video | Lang | Expected | Actual | Risk | Match | Seconds | Top reason |
|---|---|---|---|---|---|---|---|
| scam_invest_ru.mp4 | ru | investment_platform | investment_platform | 0.85 | yes | 6.7 | In speech: sounds like an investment platform pitch (model confidence 89%) |
| scam_invest_en.mp4 | en | investment_platform | investment_platform | 0.70 | yes | 2.4 | In speech: sounds like an investment platform pitch (model confidence 86%) |
| scam_betting_ru.mp4 | ru | betting | betting | 0.59 | yes | 2.2 | In speech: sounds like betting or casino promotion (model confidence 76%) |
| scam_giveaway_en.mp4 | en | giveaway | giveaway | 0.63 | yes | 2.1 | In speech: sounds like a fake giveaway (model confidence 93%) |
| scam_job_ru.mp4 | ru | job_offer | job_offer | 0.52 | yes | 2.1 | In speech: sounds like a suspicious job offer (model confidence 85%) |
| scam_pyramid_en.mp4 | en | pyramid | pyramid | 0.62 | yes | 2.2 | In speech: sounds like a pyramid or referral scheme (model confidence 94%) |
| safe_cooking_ru.mp4 | ru | none | none | 0.11 | yes | 2.0 | Rule: no typical scam signals were found |
| safe_travel_en.mp4 | en | none | none | 0.16 | yes | 1.9 | Rule: no typical scam signals were found |
| safe_warning_ru.mp4 | ru | none | none | 0.19 | yes | 2.0 | In speech: promises a high regular return (30%, 10%) |
| silent_scam_screen.mp4 | ru | investment_platform | investment_platform | 0.84 | yes | 1.1 | On screen: sounds like an investment platform pitch (model confidence 85%) |
| silent_no_text.mp4 | none | none | none | 0.00 | yes | 1.0 | Rule: no speech or on-screen text was found, so there is nothing to check |
