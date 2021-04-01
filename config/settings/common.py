"""
Django settings for acemaven project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
import datetime
from pathlib import Path
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.

PROJECT_DIR = Path(__file__).parent.resolve()
BASE_DIR = PROJECT_DIR.parent.resolve()
REPO_DIR = BASE_DIR.parent.resolve()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%2!lic16312n0yqo8ul)&-o8u-fpf1t^*7d+w%(h!!pvqurtvd'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

AUTH_USER_MODEL = 'core.CustomUser'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    'corsheaders',
    'django_filters',
    'phonenumber_field',
    'rest_framework',
    'rest_framework_jwt',
    'drf_yasg',
    'rest_auth',
    'tabbed_admin',
    'debug_toolbar',
    'channels',
    'admin_reorder',

    'app.core',
    'app.booking',
    'app.handling',
    'app.location',
    'app.websockets',
    'app.management',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),
    'DATE_FORMAT': '%d/%m/%Y',
    'DATE_INPUT_FORMATS': ['%d/%m/%Y'],
    'DATETIME_INPUT_FORMATS': ['%d/%m/%Y %H:%M', '%d/%m/%Y %H%M'],
    'DATETIME_FORMAT': '%H:%M %d %B %Y',
}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': True,
}

DATEFORMAT = "%d/%m/%Y"
DATE_INPUT_FORMATS = ['%d/%m/%Y']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'admin_reorder.middleware.ModelAdminReorder',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [
            os.path.join(BASE_DIR, "jinja2",)
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "app.core.util.templates_utils.build_jinja2_environment",
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
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

WSGI_APPLICATION = 'config.wsgi.application'

ASGI_APPLICATION = 'config.asgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/


STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = REPO_DIR / ".static"
STATIC_URL = '/assets/'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Celery
CELERY_BROKER_URL = 'redis://0.0.0.0:6379'
CELERY_RESULT_BACKEND = 'redis://0.0.0.0:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_BEAT_SCHEDULE = {
    'archive-expired-quotes': {
        'task': 'archive_quotes',
        'schedule': crontab(hour=0, minute=0),
    },
    'discard-unpaid-bookings': {
        'task': 'discard_unpaid_bookings',
        'schedule': crontab(hour=0, minute=0),
    },
    'cancel-unconfirmed-bookings': {
        'task': 'cancel_unconfirmed_bookings',
        'schedule': crontab(hour=0, minute=0),
    },
    'update-sea-operations-tracking': {
        'task': 'track_sea_operations',
        'schedule': crontab(hour='*/3', minute=0),
    },
    'delete-old-notifications': {
        'task': 'delete_old_notifications',
        'schedule': crontab(hour=0, minute=0),
    },
    'notify-users-of-expiring-surcharges': {
        'task': 'notify_users_of_expiring_surcharges',
        'schedule': crontab(hour=0, minute=0),
    },
    'notify-users-of-expiring-freight-rates': {
        'task': 'notify_users_of_expiring_freight_rates',
        'schedule': crontab(hour=0, minute=0),
    },
    'notify-users-of-import-sea-shipment-arrival': {
        'task': 'notify_users_of_import_sea_shipment_arrival',
        'schedule': crontab(hour=0, minute=0),
    },
}

# JWT
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=3),
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),
}

# Rest Auth
OLD_PASSWORD_FIELD_ENABLED = True

# Tabbed Admin
TABBED_ADMIN_USE_JQUERY_UI = True

# Channels config
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('0.0.0.0', 6379)]
        }
    }
}

# Model order in admin panel
ADMIN_REORDER = (

    {'app': 'handling',
     'label': 'AceMaven Service Revenue Settings',
     'models': ('handling.LocalFee', 'handling.GlobalFee')
     },

    {'app': 'core',
     'label': 'Accounts and Billing',
     'models': ('core.CustomUser', 'core.BankAccount', 'handling.ExchangeRate', 'booking.Transaction')
     },

    {'app': 'booking',
     'label': 'Sections',
     'models': ('booking.Booking', 'core.Company')
     },

    {'app': 'handling',
     'label': 'Platform setting',
     'models': ('handling.GeneralSetting', 'handling.ClientPlatformSetting',
                'location.Country', 'handling.Currency')
     },

    {'app': 'websockets',
     'label': 'Ticket section',
     'models': ('websockets.Ticket', 'core.SignUpRequest', 'core.Review')
     },

    {'app': 'websockets',
     'label': 'Special settings on platform (for superuser)',
     'models': ('core.Role', 'core.SignUpToken', 'auth.Group',
                'handling.AirTrackingSetting', 'handling.Airline',
                'handling.Carrier', 'handling.ContainerType',
                'handling.IMOClass', 'handling.PackagingType',
                'handling.Port', 'handling.ReleaseType',
                'handling.SeaTrackingSetting', 'handling.ShippingMode',
                'handling.ShippingType', 'booking.AdditionalSurcharge',
                'booking.Direction', 'booking.FreightRate',
                'booking.Surcharge', 'booking.TrackStatus',)
     },


)
