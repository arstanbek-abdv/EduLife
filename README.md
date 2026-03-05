# EduLife

## Деплой на Render

В корне есть **`render.yaml`** (Blueprint). Деплой через Render можно настроить так:

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint** → подключи репозиторий (или **New** → **Web Service** и укажи репо).
2. Если используешь Blueprint — Render подхватит `render.yaml`: сервис `edulife` с `rootDir: edulife`, сборка и старт из этой папки.
3. Создай **PostgreSQL** в том же проекте (Render → Add → PostgreSQL), затем в настройках веб-сервиса добавь переменную **`DATABASE_URL`** — Render подставит её из базы (Internal Database URL).
4. В **Environment** веб-сервиса задай:
   - `DJANGO_SECRET_KEY` — длинная случайная строка
   - `DJANGO_ALLOWED_HOSTS` — `*.onrender.com` или твой домен, например `edulife-xxx.onrender.com`
   - Остальное по необходимости (MinIO, SMTP и т.д.), см. `edulife/.env.example`.

Приложение уже настроено на `DATABASE_URL` и WhiteNoise для статики; порт берётся из `PORT`, который задаёт Render.