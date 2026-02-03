# Бот подборки design-вакансий + cover letter

Бот для Telegram: мониторит указанные страницы с вакансиями, фильтрует design/product/graphic design и присылает тебе ссылки с готовым cover letter под каждую вакансию (генерация через Yandex GPT).

## Что есть в проекте

- **profile.txt** — текст профиля с [danyavidmich.com/cv](https://danyavidmich.com/cv/) для генерации писем.
- **cover_letter_instruction.txt** — инструкция для Yandex GPT, как писать cover letter.
- **jobs_scraper.py** — сбор вакансий со страниц (поддержка wise.jobs и универсальный парсер).
- **yandex_gpt.py** — генерация cover letter через Yandex Cloud LLM (Ya GPT).
- **telegram_bot.py** — бот: добавление/удаление ссылок, ручная проверка, рассылка вакансий с письмами.
- **run_daily.py** — скрипт для запуска ежедневной проверки (cron).

## Настройка

### 1. Токен бота и Yandex GPT

Скопируй `.env.example` в `.env` и заполни:

```bash
cp .env.example .env
```

В `.env`:

- **TELEGRAM_BOT_TOKEN** — токен от [@BotFather](https://t.me/BotFather).
- **YANDEX_API_KEY** — API-ключ сервисного аккаунта в Yandex Cloud (роль `ai.languageModels.user`).
- **YANDEX_FOLDER_ID** — ID каталога (из `gpt://FOLDER_ID/...`). По умолчанию уже указан.
- **YANDEX_MODEL_URI** — модель, например `gpt://b1g6rst3sps7hhu8tqla/aliceai-llm/latest`.

**Важно:** не выкладывай `.env` и токены в репозиторий. Если токен бота утёк — отзови его в BotFather и создай новый.

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

## Ежедневная рассылка (cron)

Чтобы раз в день получать подборку без ручного `/check`:

1. Убедись, что хотя бы раз отправил боту `/start`.
2. Настрой cron (подставь свой путь к проекту и, при необходимости, к python):

```bash
# Каждый день в 9:00
0 9 * * * cd /Users/vidmich/Desktop/resu && . .venv/bin/activate && set -a && . .env && set +a && python run_daily.py
```

Или без venv, если пакеты установлены глобально:

```bash
0 9 * * * cd /Users/vidmich/Desktop/resu && export $(grep -v '^#' .env | xargs) && python run_daily.py
```

`run_daily.py` загружает ссылки из `data/urls.json`, вызывает скрапер, фильтрует design-вакансии, генерирует письма через Ya GPT и шлёт сообщения в чат, сохранённый по `/start`.

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
