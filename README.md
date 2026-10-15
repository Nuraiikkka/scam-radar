# Scam Radar

Загрузите видео в API: речь и надписи автоматически передаются в обученную
модель и классификатор правил. Обученная модель различает scam/legitimate;
правила определяют одну из пяти категорий, когда есть соответствующие признаки.

## Запуск

В PowerShell из корня проекта, если окружение ещё не создано:

```powershell
py -3.12 -m venv .venv
```

Установите зависимости:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements/prod.txt
```

Также нужен FFmpeg: команда `ffmpeg -version` должна выводить версию.
Whisper и EasyOCR скачивают модели при первом использовании.
Обученный файл уже находится в `artifacts/models/binary_baseline.joblib`.
Он исключён из Git; при переносе проекта скопируйте его отдельно или повторите
обучение по [инструкции](ml/README.md).

Запустите сервер:

```powershell
cd backend
$env:SCAMRADAR_MOCK = "false"
$env:SCAMRADAR_ML_ENABLED = "true"
$env:SCAMRADAR_WHISPER_MODEL = "tiny"
$env:SCAMRADAR_MAX_FRAMES = "5"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
```

Откройте http://127.0.0.1:8001/docs → `POST /analyze` → `Try it out`.
Выберите файл, очистите `url`, нажмите `Execute`. Для ссылки TikTok вместо
файла заполните `url`; скачивание ссылки зависит от доступности TikTok.
Остановка сервера: `Ctrl+C`. Перед повторным запуском остановите предыдущий.

## Как читать результат

- `verdict`: `suspected_scam` — модель или правила нашли риск;
  `insufficient_evidence` — нет достаточных признаков, безопасность не подтверждена.
- `risk_score`: максимум оценки правил и доступной оценки ML, от 0 до 1.
  Это некалиброванная оценка, а не доказанная вероятность мошенничества.
- `ml_prediction.status`: `ok` означает, что модель выполнила прогноз.
- `ml_prediction.verdict`: бинарный прогноз `scam` / `legitimate`.
- `ml_prediction.score` и `threshold`: оценка модели и выбранный на validation порог.
- `category`: категория по правилам — `investment_platform`, `pyramid`,
  `betting`, `giveaway`, `job_offer` или `none`. Если ML видит риск, а правила
  не определили тип, категория остаётся `none`, но `verdict` — `suspected_scam`.
  Поле `assessment.category_determined` явно показывает, определён ли тип.
- `reasons`: признаки правил; это не объяснение работы ML.
- `transcript`, `ocr_text`: фактически извлечённая речь и надписи.
- `assessment.warnings`: ограничения анализа и проблемы доступности модели.

Новый ML-прогноз сохраняется вместе с результатом в SQLite. История доступна
через `GET /analyses`, один результат — `GET /analyses/{id}`. Старые результаты
не пересчитываются: для них `ml_prediction.status` равен `not_recorded`.
Существующая база не удаляется; при запуске добавляется таблица прогнозов.

Если файл модели отсутствует или повреждён, API использует правила и сообщает
`model_missing` / `model_error`; при нехватке текста — `insufficient_text`.
Для отключения ML задайте `SCAMRADAR_ML_ENABLED=false` и перезапустите сервер.
`SCAMRADAR_MOCK=true` включает демонстрационные ответы без анализа.
Журнал ошибок: `backend/logs/app.log`. Запускайте сервер из `backend`, чтобы
использовать одну и ту же SQLite-базу.

## Структура

- `backend/app/services/` — речь, OCR, правила, ML и объединение результатов.
- `backend/app/routers/` — загрузка видео, история, обратная связь и статистика.
- `backend/tests/` — тесты API, правил и подключения ML.
- `ml/` — сбор данных, обучение и дополнительная проверка текста из терминала.
- `data/` — локальные данные обучения, исключены из Git.
- `artifacts/models/` — локальная обученная модель, исключена из Git.
- `reports/` — аудит данных, метрики и состав тестовой выборки.

## Проверки и обучение

Из папки `backend`:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
```

Из корня проекта:

```powershell
.\.venv\Scripts\python.exe -m pytest ml/tests -q
```

[Обучение и проверка своего текста](ml/README.md).
[Аудит датасета и результаты эксперимента](reports/dataset_audit.md).
Модель экспериментальная: небольшой набор crypto/giftcard, частично
автоматические метки, без подтверждённой точности для всех пяти категорий,
русского/казахского языка и новых TikTok-роликов. Лицензия данных CC BY-NC-SA 4.0.
