"""
Django settings for cantusdata project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

from pathlib import Path
import os

is_development = os.environ.get("DEVELOPMENT") == "True"
is_production = not is_development

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = is_development

ALLOWED_HOSTS = [
    "cantus.simssa.ca",
    "dev-cantus.simssa.ca",
    "cantus.staging.simssa.ca",
    "localhost",
    "cantus-app-1",
]

# Application definition

INSTALLED_APPS = (
    # Template apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Additional apps
    "django_celery_results",
    "rest_framework",
    "rest_framework.authtoken",
    "cantusdata.CantusdataConfig",
)

if DEBUG:
    INSTALLED_APPS += ("django_extensions",)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",  # Migration: + django 3.1
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

ROOT_URLCONF = "cantusdata.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "cantusdata.context_processors.export_vars",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cantusdata.wsgi.application"


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": "postgres",
        "PORT": "5432",
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_URL_NEUMEEDITOR = "/neumeeditor/media/"

# This needs to be an absolute path to the file system location
STATIC_ROOT = BASE_DIR / "../static"
MEDIA_ROOT = BASE_DIR / "media/"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        # "rest_framework_jsonp.renderers.JSONPRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    # 'DEFAULT_PERMISSION_CLASSES': [
    #     'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    # ]
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

SOLR_SERVER = "http://solr:8983/solr/cantus_ultimus_1"
SOLR_ADMIN = "http://solr:8983/solr/admin"
SOLR_TEST_SERVER = "http://solr:8983/solr/cantus-test"

LOGGING_CONFIG = None

# AUTHENTICATION
MAX_TOKEN_AGE_DAYS = 3

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SESSION_COOKIE_SECURE = is_production
CSRF_COOKIE_SECURE = is_production
CSRF_TRUSTED_ORIGINS = ["https://cantus.simssa.ca", "https://cantus.staging.simssa.ca"]

SECURE_HSTS_SECONDS = 86400
SECURE_HSTS_INCLUDE_SUBDOMAINS = is_production
SECURE_HSTS_PRELOAD = is_production

CELERY_BROKER_URL = f"amqp://{os.environ.get('RABBIT_USER')}:{os.environ.get('RABBIT_PASSWORD')}@cantus-rabbitmq-1:5672/{os.environ.get('RABBIT_VHOST')}"
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_PERSISTENT = False
CELERY_RESULT_EXTENDED = True
CELERY_APP = "cantusdata"
CELERY_TASK_TRACK_STARTED = True
