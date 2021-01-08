"""
Django settings for cantusdata project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "+lf0*we_nuqy(y5gxx4g@v^#&um83gh0*g6_ro)1l_6#k72j^^"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


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
    "rest_framework",
    "rest_framework.authtoken",
    "cantusdata",
    "django_extensions",
    "coverage",
)

# Migration: In django 3.1 "MIDDLEWARE_CLASSES" -> "MIDDLEWARE"
# Migration: Preserving both for now. Remove "MIDDLEWARE_CLASSES" when migration is complete
MIDDLEWARE = MIDDLEWARE_CLASSES = (
    # "django.middleware.security.SecurityMiddleware" # Migration: + django 3.1
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

ROOT_URLCONF = "urls"

# Migration: TEMPLATES + django 3.1
# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

WSGI_APPLICATION = "cantusdata.wsgi.application"


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "cantus_db",
        "USER": "cantus_admin",
        "PASSWORD": "Pl4c3H0ld3r",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Migration: + django 3.1
# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
#
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]

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
STATIC_ROOT = BASE_DIR / "cantusdata/static"
MEDIA_ROOT = BASE_DIR / "media/"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
}

SOLR_SERVER = "http://localhost:8983/solr/collection1"
SOLR_ADMIN = "http://localhost:8983/solr/admin"
SOLR_TEST_SERVER = "http://localhost:8983/solr/cantus-test"

LOGGING_CONFIG = None

# AUTHENTICATION
MAX_TOKEN_AGE_DAYS = 3
