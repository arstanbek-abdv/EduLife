# EduLife

Платформа для онлайн-обучения: каталог курсов, запись студентов, модули и задания, отзывы и хранение файлов.

---

## Стек

| Категория | Технологии |
|-----------|-------------|
| Backend | Python 3.12, Django 6, Django REST Framework |
| Аутентификация | JWT (Simple JWT), сброс пароля по email |
| БД | PostgreSQL (локально и в проде) |
| Файлы | MinIO / S3-совместимое хранилище (django-storages, boto3) |
| Документация API | Swagger / ReDoc (drf-yasg) |
| Статика в проде | WhiteNoise |
| Деплой | Render (см. `render.yaml`) |

---

## Основной функционал

- **Пользователи**: регистрация, роли (Студент, Учитель, Админ), профиль, аватар, сброс пароля по email.
- **Курсы**: создание учителями, черновик/публикация, обложка, категории, модули и задания (документ/видео), загрузка файлов в MinIO.
- **Студенты**: каталог курсов, запись на курс и отписка, «Мои курсы», прохождение заданий (отметка выполнения), отзывы и рейтинг (1–5).
- **API**: REST, JWT-токены, Swagger на `/swagger/`, ReDoc на `/redoc/`. Руководство для фронтенда: [docs/API.md](docs/API.md).

---

## Локальный запуск

```bash
cd edulife
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # заполни переменные
python manage.py migrate
python manage.py runserver
```

С БД и MinIO через Docker:

```bash
cd edulife
docker compose up -d
# затем миграции и runserver (или используй entrypoint при запуске приложения в контейнере)
```

Переменные окружения — в `edulife/.env.example` (PostgreSQL, MinIO, Django, SMTP для сброса пароля).

---

## Деплой на Render

В корне репозитория лежит **`render.yaml`** (Blueprint).

### Шаги

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Web Service** (или **Blueprint**), подключи репозиторий.
2. У сервиса укажи **Root Directory**: `edulife`. Сборка и старт будут из этой папки.
3. Добавь **PostgreSQL** в проект, в настройках веб-сервиса пропиши **`DATABASE_URL`** (Internal Database URL из базы).
4. В **Environment** задай:
   - `DJANGO_SECRET_KEY` — длинная случайная строка
   - `DJANGO_ALLOWED_HOSTS` — `.onrender.com` (подойдёт любой URL вида `*-xxx.onrender.com`) или точный хост, например `edulife-abc12.onrender.com`
   - при необходимости MinIO и SMTP — по образцу из `edulife/.env.example`

Приложение использует `DATABASE_URL`, WhiteNoise и порт из `PORT`.

### Как выглядят URL на Render

После деплоя Render выдаёт сервису адрес вида **`https://<имя-сервиса>.onrender.com`** (имя задаётся при создании или автоматически).

| Назначение | URL |
|------------|-----|
| Базовый адрес бэкенда | `https://<имя-сервиса>.onrender.com` |
| Базовый URL для API (для фронта) | `https://<имя-сервиса>.onrender.com/api/` |
| Swagger UI (документация API) | `https://<имя-сервиса>.onrender.com/swagger/` |
| ReDoc (альтернативная документация) | `https://<имя-сервиса>.onrender.com/redoc/` |
| Логин API | `POST https://<имя-сервиса>.onrender.com/api/users/login/` |

Пример: если сервис называется `edulife`, то чаще всего будет `https://edulife.onrender.com` (или с суффиксом вроде `edulife-xyzab.onrender.com`). Точный URL всегда виден в Render Dashboard у сервиса.

### Как фронт получает доступ к Swagger

- **Swagger и ReDoc доступны без авторизации** — по ссылкам выше любой может открыть документацию в браузере.
- Фронту достаточно подставить в конфиг **базовый URL API**: `https://<имя-сервиса>.onrender.com` (без `/api/` в конце — эндпоинты уже с префиксом `/api/...`). Например:
  - логин: `POST ${BASE_URL}/api/users/login/`
  - каталог: `GET ${BASE_URL}/api/courses/catalog/`
- Для тестов и отладки фронт может открывать Swagger в браузере по `https://<имя-сервиса>.onrender.com/swagger/`, выполнять запросы из интерфейса и копировать токен в «Authorize» для проверки защищённых эндпоинтов.
