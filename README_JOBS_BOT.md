# Бот подборки design-вакансий + cover letter

Бот для Telegram: мониторит указанные страницы с вакансиями, фильтрует design/product/graphic design и присылает тебе ссылки с готовым cover letter под каждую вакансию (генерация через Yandex GPT).

## Что есть в проекте

- **profile.txt** — текст профиля с [danyavidmich.com/cv](https://danyavidmich.com/cv/) для генерации писем.
- **cover_letter_instruction.txt** — инструкция для Yandex GPT, как писать cover letter.
- **jobs_scraper.py** — сбор вакансий со страниц (поддержка wise.jobs и универсальный парсер).
- **yandex_gpt.py** — генерация cover letter через Yandex Cloud LLM (Ya GPT).
- **telegram_bot.py** — бот: добавление/удаление ссылок, ручная проверка, рассылка вакансий с письмами.
- **run_daily.py** — скрипт для запуска ежедневной проверки (cron или GitHub Actions).
- **.github/workflows/daily-jobs.yml** — ежедневный запуск через GitHub Actions с секретами.
- **.github/workflows/deploy-to-bucket.yml** — деплой содержимого репо в бакет Yandex Object Storage при push в `main`.

## Секреты GitHub

Ежедневная проверка вакансий запускается в GitHub Actions. Все чувствительные данные хранятся в **секретах репозитория**.

1. Открой репозиторий на GitHub → **Settings** → **Secrets and variables** → **Actions**.
2. Нажми **New repository secret** и добавь секреты:

| Имя секрета | Описание |
|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather). |
| `TELEGRAM_CHAT_ID` | ID чата, куда слать сообщения. Как получить: напиши боту `/start` (локально с `.env`), затем открой `https://api.telegram.org/bot<TOKEN>/getUpdates` — в ответе будет `"chat":{"id":123456789}`. |
| `YANDEX_API_KEY` | Секретный ключ сервисного аккаунта Yandex Cloud (роль `ai.languageModels.user`). |
| `YANDEX_FOLDER_ID` | ID каталога, например `b1g6rst3sps7hhu8tqla`. |
| `YANDEX_MODEL_URI` | URI модели, например `gpt://b1g6rst3sps7hhu8tqla/aliceai-llm/latest`. |
| `YANDEX_S3_BUCKET` | Имя бакета Object Storage, например `jobs-for-danya`. |
| `YANDEX_S3_ACCESS_KEY_ID` | Access Key ID статического ключа сервисного аккаунта (доступ к бакету). |
| `YANDEX_S3_SECRET_ACCESS_KEY` | Секретный ключ статического ключа. |

После добавления секретов workflow **Daily jobs digest** будет запускаться по расписанию (каждый день в 9:00 UTC) и присылать новые design-вакансии с cover letter в Telegram. Ручной запуск: **Actions** → **Daily jobs digest** → **Run workflow**.

Состояние (уже отправленные вакансии) хранится в `data/seen_jobs.json` в репозитории — workflow сам коммитит обновления после каждого запуска.

**Деплой в бакет:** при каждом push в ветку `main` workflow **Deploy to bucket** синхронизирует содержимое репозитория в бакет Yandex Object Storage (без `.git`, `.env`, `.venv`, `.github`). Ручной запуск: **Actions** → **Deploy to bucket** → **Run workflow**. Нужны секреты `YANDEX_S3_BUCKET`, `YANDEX_S3_ACCESS_KEY_ID`, `YANDEX_S3_SECRET_ACCESS_KEY`.

## Настройка (локальный запуск бота)

Для работы с ботом в Telegram (команды `/addurl`, `/removeurl`, `/check` и т.д.) запускай его локально.

### 1. Переменные окружения

Скопируй `.env.example` в `.env` и заполни (или используй те же значения, что и в секретах GitHub):

```bash
cp .env.example .env
```

В `.env`:

- **TELEGRAM_BOT_TOKEN** — токен от [@BotFather](https://t.me/BotFather).
- **YANDEX_API_KEY** — секретный ключ сервисного аккаунта Yandex Cloud.
- **YANDEX_FOLDER_ID** — ID каталога (по умолчанию уже указан в примере).
- **YANDEX_MODEL_URI** — модель (по умолчанию уже указана).

**Важно:** `.env` в `.gitignore`, в репозиторий не попадает. Секреты для CI храни только в GitHub Secrets.

### 2. Зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Запуск бота

```bash
# Загрузить переменные из .env
export $(grep -v '^#' .env | xargs)
# или: source .env (если в .env нет export)
python telegram_bot.py
```

В Telegram: найди бота, отправь `/start`. После этого бот будет присылать подборки в этот чат.

## Команды бота

| Команда | Описание |
|--------|----------|
| `/start` | Сохранить чат и показать справку |
| `/addurl <ссылка>` | Добавить страницу с вакансиями (например https://wise.jobs/jobs) |
| `/removeurl <ссылка>` | Удалить ссылку из списка |
| `/listurls` | Показать все ссылки |
| `/check` | Сейчас проверить все ссылки и прислать новые design-вакансии с cover letter |
| `/help` | Краткая справка |

Ссылки хранятся в `data/urls.json`. Уже просмотренные вакансии — в `data/seen_jobs.json`, повторно не присылаются.

## Ежедневная рассылка

- **Через GitHub (рекомендуется):** добавь секреты в репозитории (см. выше). Workflow запускается каждый день в 9:00 UTC и сам обновляет `data/seen_jobs.json` в репо.
- **Локально (cron):** если не используешь GitHub Actions, задай в секрете `TELEGRAM_CHAT_ID` свой chat id и настрой cron:

```bash
0 9 * * * cd /path/to/resu && . .venv/bin/activate && set -a && . .env && set +a && python run_daily.py
```

`run_daily.py` читает ссылки из `data/urls.json`, вызывает скрапер, фильтрует design-вакансии, генерирует письма через Ya GPT и шлёт сообщения в чат (из `TELEGRAM_CHAT_ID` в CI или из `data/bot_state.json` после `/start` локально).

## Фильтр вакансий

Учитываются вакансии, где в названии, команде (team) или описании встречаются:  
design, product design, graphic design, ux, ui, brand, creative, art director, visual design, design lead, designer.  
Список можно изменить в `config.py` (`DESIGN_KEYWORDS`).

## Резюме и письма

- В сообщениях бот подставляет ссылку на резюме: **https://danyavidmich.com/cv_vidmich_designer.pdf**
- Текст для писем берётся из **profile.txt**; логика генерации задаётся в **cover_letter_instruction.txt**.

## Если wise.jobs не отдаёт вакансии

Страница wise.jobs может подгружать список вакансий через JavaScript. В этом случае простой парсер по HTML может ничего не найти. Варианты:

- Добавить в бота другие сайты с вакансиями (через `/addurl`); универсальный парсер ищет ссылки с design-контекстом.
- Позже можно добавить парсер с Playwright/Selenium для JS-страниц или использовать официальный API сайта, если он есть.

## Структура данных

- `data/urls.json` — список URL для мониторинга.
- `data/seen_jobs.json` — ID уже отправленных вакансий (чтобы не дублировать).
- `data/bot_state.json` — chat_id пользователя после `/start`.

Все пути можно поменять в `config.py`.
