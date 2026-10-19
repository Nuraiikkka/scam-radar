# Гайд для Айсулу: компьютерное зрение и ML (главная по этой части)

## Твоя зона

Ты главная по всей части CV и ML. С CV тебе помогает Нурай: пишет тесты для правил,
проверяет OCR на реальных видео, замеряет скорость. Решения о том, как это работает, принимаешь ты.

- `backend/app/services/vision_frames.py` — берём кадры из видео.
- `backend/app/services/vision_ocr.py` — читаем текст на кадрах (EasyOCR, русский и английский).
- `backend/app/services/vision_rules.py` — правила: ссылки, Telegram, телефоны, проценты, деньги, QR.
- `backend/app/services/vision.py` — собирает кадры, OCR, QR и правила в один результат.
- `backend/app/services/text_classifier.py` — классификатор текста и ключевые слова.
- `backend/app/services/fusion.py` — итоговый риск, категория и причины.
- `backend/app/services/pipeline.py` — порядок шагов анализа.
- `backend/ml/train_text.py`, `backend/ml/evaluate.py`, папка `data/`.

## Как проходит анализ

1. Речь (бэкенд Нурай и Мольдир, `audio.py`) и кадры приходят в `pipeline.analyze_local_video()`.
2. `sample_frames()` берёт кадр каждые `SCAMRADAR_FRAME_INTERVAL_SECONDS` (2 с), не больше
   `SCAMRADAR_MAX_FRAMES` (12), пропускает одинаковые кадры и уменьшает их до 720 пикселей.
3. `read_frames()` читает текст EasyOCR, строки с уверенностью ниже 0.3 выбрасываются.
4. `vision_rules.analyze_text()` ищет признаки и для каждого делает причину с источником:
   «В речи», «На экране», «В QR-коде». `normalize_text()` исправляет ошибки OCR (`tmelx` → `t.me/x`).
5. `text_classifier.classify_text()` даёт вероятности категорий (TF-IDF + логистическая регрессия).
6. `fusion.fuse()` складывает оценку текста и экрана с весами `SCAMRADAR_FUSION_TEXT_WEIGHT` и
   `SCAMRADAR_FUSION_VISION_WEIGHT`. Ниже порога `SCAMRADAR_FUSION_NONE_THRESHOLD` (0.35) — категория `none`.

Модели Whisper и EasyOCR скачиваются один раз в том Docker `models`.

## Обучение и проверка (в папке `backend`)

```
python ml/train_text.py --version v1.1.0
python ml/evaluate.py
```

Скрипт печатает accuracy, precision/recall/F1 и матрицу ошибок. Тестовые шаблоны не попадают
в обучение, поэтому цифры честные. Сейчас (v1.0.0): 800 синтетических примеров, macro F1 0.801,
по 4 фолдам 0.822. Слабое место — «инвестиции» против «ставок». Новые цифры — в `docs/ML.md`.

## Тесты

Из корня репозитория, когда `docker compose up -d` уже запущен:

```
docker build -t scamradar-backend:dev --build-arg REQUIREMENTS=dev.txt backend
docker run --rm --network scamradar_default -v "$PWD:/repo" -v scamradar_models:/models -w /repo/backend -e TEST_REDIS_URL=redis://redis:6379/15 -e TEST_MODEL_CACHE_DIR=/models/cache --entrypoint python scamradar-backend:dev -m pytest
```

Правила: `tests/test_vision_rules.py`. Классификатор и fusion: `tests/test_text_and_fusion.py`.
Кадры и видео целиком: `tests/test_worker_and_media.py`, `tests/test_full_pipeline.py`.

## Как добавить новое правило

1. Добавь выражение или слово в `vision_rules.py`, причину сделай через `make_cue(...)` на двух языках.
2. Добавь тест в `tests/test_vision_rules.py`.
3. `ruff check .` и `ruff format .` в папке `backend`.

## Работа в команде

- Ветка: `cv/feat-...` или `ml/feat-...`. Коммит: `feat(cv): ...` или `feat(ml): ...`.
- Твои PR проверяет Мольдир, ты проверяешь PR Нурай. Нурай тоже code owner файлов CV.
