"""
URL configuration for edulife project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt import views as jwt_views


API_DESCRIPTION = """
## Интеграция для фронтенда

**Базовый URL:** все эндпоинты под префиксом `/api/` (пользователи: `/api/users/`, курсы: `/api/courses/`).

**Аутентификация:**
1. `POST /api/users/login/` — тело `{"username": "...", "password": "..."}` → в ответе `access` и `refresh`.
2. В каждый запрос (кроме login, register, forgot-password, catalog без авторизации) добавляйте заголовок:  
   `Authorization: Bearer <access>`
3. При истечении access (401) вызовите `POST /api/token/refresh/` с телом `{"refresh": "<refresh_token>"}` → новый `access`.
4. Выход: `POST /api/users/logout/` с телом `{"refresh": "<refresh_token>"}` (токен будет в чёрном списке).

**Пагинация:** списки возвращают объекты с полями `count`, `next`, `previous`, `results` (размер страницы по умолчанию: 20).

**Загрузка файлов:** используйте `multipart/form-data`, поле файла — `file` (аватар, обложка курса, файл задания).

**Документация:** Swagger UI — `/swagger/`, ReDoc — `/redoc/`. В Swagger нажмите «Authorize» и вставьте access token (без слова Bearer).  
Подробное руководство для фронтенда: репозиторий → `docs/API.md`.
"""
schema_view = get_schema_view(
    openapi.Info(
        title="EduLife API",
        default_version="v1",
        description=API_DESCRIPTION,
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/', include('apps.users.urls')), # users/urls
    path('api/courses/',include('apps.courses.urls')),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0)),
]

