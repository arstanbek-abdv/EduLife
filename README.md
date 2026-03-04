# EduLife

## Деплой на Railway

В корне репозитория лежат `requirements.txt`, `start.sh` и `start.py`, чтобы Railpack определил проект как Python и нашёл скрипт запуска. Сборка идёт из корня, запуск выполняется из папки `edulife/`.

**Переменные окружения** в Railway задай по образцу из `edulife/.env.example` (в т.ч. `POSTGRES_*`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` с твоим доменом Railway).