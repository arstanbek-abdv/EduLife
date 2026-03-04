# EduLife

## Деплой на Railway

Проект настроен для деплоя на Railway. Корневая директория для сборки — `edulife/`.

**Если при деплое появляется ошибка** «Railpack could not determine how to build» или «Script start.sh not found»:

1. В [Railway Dashboard](https://railway.app/dashboard) открой свой проект и сервис.
2. **Settings** → **Root Directory** укажи: `edulife` (без слэша).
3. Сохрани и сделай **Redeploy**.

После этого Railpack будет собирать приложение из папки `edulife/` (там есть `requirements.txt`, `manage.py`), а запуск пойдёт по `Procfile` или `start.sh`.

**Переменные окружения** в Railway задай по образцу из `edulife/.env.example` (в т.ч. `POSTGRES_*`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` с твоим доменом Railway).