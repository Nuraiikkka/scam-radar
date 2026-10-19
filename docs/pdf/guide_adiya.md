# Гайд для Адии: Flutter и UX

## Твоя зона

- `frontend/` — приложение для Android, iOS и Web.
- `e2e/` — браузерные тесты Playwright и кравлер.

## Структура

- `lib/features/` — экраны: onboarding, home, analysis (прогресс и результат), history, stats, settings, auth, shell.
- `lib/data/` — модели (точно как в API), клиент dio с обновлением токена, `local_store.dart`.
- `lib/state/providers.dart` — состояние на Riverpod: настройки, вход, история, статистика.
- `lib/widgets/` — общие виджеты: загрузка, пусто, ошибка, офлайн, шкала риска, значок категории.
- `lib/theme/tokens.dart` — цвета, отступы, радиусы. Не пиши цвета прямо в экранах.
- `lib/l10n/app_ru.arb`, `app_en.arb` — все тексты. Новый текст добавляй в оба файла.

## Запуск

```
flutter run -d chrome --web-port 8091 --dart-define-from-file=env/local.json
```

Сервер нужен запущенный (`docker compose up`). Для телефона в той же сети поменяй адрес
сервера в Настройках → «Адрес сервера». Окружения: `env/local.json`, `staging.json`, `prod.json`.

## Тесты

```
flutter analyze
flutter test
```

Тесты экранов лежат в `integration_test/screens/`. Каждый тест назван по ID из `docs/SCREENS.md`.
Если добавляешь кнопку — добавь строку в `SCREENS.md` и тест с тем же ID.
В браузере: `flutter drive --driver=test_driver/integration_test.dart --target=integration_test/app_test.dart -d web-server --browser-name=chrome --headless`
(нужен `chromedriver --port=4444`).

Контракт с API: `test/contract/openapi_contract_test.dart`. Если упал — модель не совпадает с сервером.

## Правила UX

- На каждом экране есть загрузка, пусто, ошибка с кнопкой «Повторить» и офлайн-баннер.
- Кнопки не меньше 48×48, у иконок есть `tooltip`, тексты влезают при крупном шрифте (тест A11Y).
- Ничего не обещаем: результат — «оценка риска, а не приговор».

## Сборка

- Web: `flutter build web --release --dart-define-from-file=env/prod.json` (в Docker это делает `frontend/Dockerfile`).
- Android: `flutter build appbundle --release --dart-define=API_BASE_URL=https://домен`. Подпись — файл `android/key.properties`.
- iOS: на Mac с Xcode `flutter build ipa --release --dart-define=API_BASE_URL=https://домен`.

## Работа в команде

- Ветка: `frontend/feat-...`. Коммит: `feat(frontend): ...`.
- Твои PR проверяет Нурай, ты проверяешь PR Мольдир.
