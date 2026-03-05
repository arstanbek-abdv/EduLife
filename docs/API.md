# EduLife API — руководство для фронтенда

Краткое руководство по интеграции с бэкендом EduLife. Полная схема запросов/ответов и тестирование — в **Swagger** и **ReDoc** (ссылки ниже).

---

## Базовый URL и префиксы

- Все API под префиксом **`/api/`**.
- Пользователи и авторизация: **`/api/users/`**.
- Курсы, модули, задания, отзывы: **`/api/courses/`**.
- Обновление JWT: **`/api/token/refresh/`**.

**Локально:** `http://localhost:8000`.

**Прод (Render):** после деплоя бэкенд доступен по адресу вида `https://<имя-сервиса>.onrender.com` (точный URL в Render Dashboard). Тогда:
- базовый URL для запросов: `https://<имя-сервиса>.onrender.com`
- **Swagger (документация и тесты):** `https://<имя-сервиса>.onrender.com/swagger/` — открывается в браузере без логина, можно вызывать API и вставить токен в «Authorize»
- **ReDoc:** `https://<имя-сервиса>.onrender.com/redoc/`
- пример логина: `POST https://<имя-сервиса>.onrender.com/api/users/login/`

В конфиге фронта задайте одну переменную (например `VITE_API_BASE_URL` или `REACT_APP_API_BASE_URL`) равной этому базовому URL; эндпоинты собирайте как `${API_BASE_URL}/api/...`.

---

## Аутентификация (JWT)

### 1. Вход

```http
POST /api/users/login/
Content-Type: application/json

{"username": "user", "password": "password"}
```

**Ответ 200:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

- **access** — передавать в заголовке `Authorization: Bearer <access>` при каждом запросе к защищённым эндпоинтам.
- **refresh** — использовать только для обновления access или для logout.

### 2. Заголовок для защищённых запросов

```http
Authorization: Bearer <access_token>
```

Слово `Bearer` и пробел обязательны. Не отправляйте refresh в этом заголовке.

### 3. Обновление access (при 401)

```http
POST /api/token/refresh/
Content-Type: application/json

{"refresh": "<refresh_token>"}
```

**Ответ 200:** `{"access": "новый_access_token"}`. Старый refresh после ротации может быть недействителен — сохраняйте новый из ответа, если бэкенд его вернёт.

### 4. Выход

```http
POST /api/users/logout/
Content-Type: application/json
Authorization: Bearer <access_token>

{"refresh": "<refresh_token>"}
```

Refresh-токен попадает в чёрный список; повторно использовать его нельзя.

### 5. Регистрация (без токена)

```http
POST /api/users/register/
Content-Type: application/json

{
  "username": "student1",
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "Имя",
  "last_name": "Фамилия"
}
```

Роль по умолчанию — студент. После регистрации пользователь может войти через `/api/users/login/`.

### 6. Сброс пароля

- Запрос ссылки: `POST /api/users/forgot-password/` с телом `{"email": "user@example.com"}`.
- Установка нового пароля: `POST /api/users/reset-password/<token>/` с телом `{"password": "new_password"}` (токен из письма).

---

## Пагинация

Списки (каталог, отзывы, модули, задания и т.д.) возвращают объект вида:

```json
{
  "count": 100,
  "next": "https://.../api/courses/catalog/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

Размер страницы по умолчанию: **20**. Параметр страницы: **`page`** (например, `?page=2`).

---

## Эндпоинты по разделам

### Пользователи (`/api/users/`)

| Метод | Путь | Описание | Авторизация |
|-------|------|----------|-------------|
| POST | `/login/` | Вход, получение access/refresh | — |
| POST | `/logout/` | Выход (blacklist refresh) | Bearer |
| POST | `/register/` | Регистрация | — |
| POST | `/forgot-password/` | Запрос сброса пароля | — |
| POST | `/reset-password/<token>/` | Установка нового пароля | — |
| GET/PATCH | `/edit-profile/` | Текущий пользователь: просмотр/редактирование | Bearer |
| GET | `/my-profile/` | Профиль текущего пользователя (с URL аватара) | Bearer |
| POST | `/profile-image/` | Загрузка аватара | Bearer |
| GET | `/teacher-profiles/<id>/` | Публичный профиль преподавателя | опционально |

### Загрузка аватара и файлов

Все загрузки — **`multipart/form-data`**, поле с файлом: **`file`**.

Пример (аватар):

```http
POST /api/users/profile-image/
Authorization: Bearer <access>
Content-Type: multipart/form-data; boundary=----...

------...
Content-Disposition: form-data; name="file"; filename="avatar.jpg"
Content-Type: image/jpeg

<binary>
------...
```

Аналогично: обложка курса, файл задания — везде поле **`file`**.

### Курсы (`/api/courses/`)

| Метод | Путь | Описание | Авторизация |
|-------|------|----------|-------------|
| GET | `/catalog/` | Список опубликованных курсов | опционально |
| GET | `/catalog/<course_id>/` | Один опубликованный курс | опционально |
| GET | `/my-courses/` | Мои курсы (студент — записанные, учитель — свои) | Bearer |
| POST | `/new-course/` | Создать курс (учитель) | Bearer |
| PATCH/DELETE | `/new-course/<id>/` | Редактировать/удалить курс | Bearer |
| POST | `/new-course/<course_id>/modules/` | Добавить модуль | Bearer |
| PATCH/DELETE | `/new-course/<course_id>/modules/<id>/` | Редактировать/удалить модуль | Bearer |
| POST | `/modules/<module_id>/tasks/` | Добавить задание | Bearer |
| PATCH/DELETE | `/modules/<module_id>/tasks/<id>/` | Редактировать/удалить задание | Bearer |
| POST | `/tasks/<task_id>/upload/` | Загрузить файл к заданию (multipart, поле `file`) | Bearer |
| GET | `/tasks/<task_id>/file/` | Получить URL/инфо файла задания | Bearer |
| POST | `/tasks/<task_id>/complete/` | Отметить задание выполненным (студент) | Bearer |
| POST | `/<course_id>/cover/` | Загрузить обложку курса (multipart, поле `file`) | Bearer |
| POST | `/<course_id>/publish/` | Опубликовать курс | Bearer |
| POST | `/<course_id>/enroll/` | Записаться на курс | Bearer |
| POST | `/<course_id>/unenroll/` | Отписаться от курса | Bearer |

### Отзывы, модули, задания (ViewSet)

| Метод | Путь | Описание |
|-------|------|----------|
| GET/POST | `/reviews/` | Список отзывов / создать отзыв |
| GET/PATCH/DELETE | `/reviews/<id>/` | Один отзыв |
| GET/POST | `/modules/` | Список модулей / создать (контекст курса через query) |
| GET/PATCH/DELETE | `/modules/<id>/` | Один модуль |
| GET/POST | `/tasks/` | Список заданий / создать |
| GET/PATCH/DELETE | `/tasks/<id>/` | Одно задание |

Точные query-параметры и тела запросов смотри в Swagger/ReDoc.

---

## Формат ошибок

- **400 Bad Request** — ошибки валидации, обычно тело вида: `{"field": ["сообщение"]}` или `{"detail": "..."}`.
- **401 Unauthorized** — нет или неверный/истёкший access. Нужно обновить токен через `/api/token/refresh/` или заново войти.
- **403 Forbidden** — доступ запрещён (не та роль, не свой ресурс).
- **404 Not Found** — объект не найден, часто `{"detail": "Not found."}`.

---

## Файлы и ссылки на контент

- В ответах поля вроде `profile_picture_url`, `file_url`, `cover_image` и т.п. содержат **временные подписанные URL** (MinIO/S3). Ссылку нужно использовать как есть (например, в `<img src="...">` или редирект на скачивание); подпись имеет ограниченный срок жизни (например, 1 час).
- Загрузка файлов всегда идёт через Django (на бэкенд), скачивание — по выданной ссылке напрямую с хранилища.

---

## Чек-лист интеграции

1. Базовый URL хранить в конфиге (dev/prod).
2. После логина сохранять `access` и `refresh` (например, в памяти или безопасном хранилище).
3. В HTTP-клиент по умолчанию добавлять заголовок `Authorization: Bearer <access>` для всех запросов к `/api/`, кроме login, register, forgot-password и публичного catalog.
4. При ответе 401: вызвать refresh; при успехе — повторить исходный запрос с новым access; при ошибке refresh — редирект на страницу входа.
5. Загрузки (аватар, обложка, файл задания) — `multipart/form-data`, поле **`file`**.
6. Списки обрабатывать как объекты с `results` и опционально `next`/`previous` для пагинации.

Детальные схемы полей запроса и ответа — в **Swagger** (`/swagger/`) и **ReDoc** (`/redoc/`).
