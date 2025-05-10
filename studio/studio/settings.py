"""
Django settings for studio project.
... (остальные импорты и BASE_DIR) ...
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-13vj1eqs^@^jrx6a*m0l9kv-r04_%ubaqof=271u9r2=@vvr!c'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [ 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters', 
    'app_studio',
]


AUTH_USER_MODEL = 'app_studio.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'studio.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'studio.wsgi.application'


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
]

AUTHENTICATION_BACKENDS = [
    'app_studio.backends.EmailOrUsernameBackend', # мое
    'django.contrib.auth.backends.ModelBackend', # Стандарт
]

REST_FRAMEWORK = {
    # --- АУТЕНТИФИКАЦИЯ ---
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication', # Для браузера и админки
        'rest_framework.authentication.BasicAuthentication', # Для тестов/простых скриптов 
    ),
    # --- ПРАВА ДОСТУПА ---
    'DEFAULT_PERMISSION_CLASSES': (
        # По умолчанию требуем аутентификацию для всех запросов, кроме безопасных (GET, HEAD, OPTIONS)
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    # --- ПАГИНАЦИЯ ---
    # !!! Включаем пагинацию по умолчанию !!!
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10, 

    # --- ФИЛЬТРАЦИЯ ---
    # Указываем бэкенд для django-filter 
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
        ),


}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    #{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    { # Оставить проверку минимальной длины 
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6, 
        }
    },
    #{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    #{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
