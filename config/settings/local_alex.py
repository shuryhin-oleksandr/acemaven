from config.settings.common import *

ALLOWED_HOSTS = ["*", ]
# INTERNAL_IPS = ['127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'acemaven_database',
        'USER': 'postgres',
        'HOST': 'localhost',
        'PASSWORD': 'acemaven1234',
        'PORT': '5432',
    }
}


ADMIN_EMAILS = []

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'outlook.office365.com'
EMAIL_HOST_USER = 'alertas@acemaven.com'
EMAIL_HOST_PASSWORD = '4cem4v3n$**'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

DOMAIN_ADDRESS = 'http://18.230.134.205:80/'
DOMAIN_ADDRESS_CHAT = 'http://18.230.134.205'

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = ['http://18.230.134.205','https://acemaven.s3.amazonaws.com',]
CORS_ORIGIN_REGEX_WHITELIST = ['*',]

STATIC_LOCATION = 'static'
PUBLIC_MEDIA_LOCATION = 'media'
AWS_QUERYSTRING_AUTH = False
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_REGION_NAME = "us-east-2"
AWS_ACCESS_KEY_ID = "AKIAUUDQFF2QHANGSG74"
AWS_S3_OBJECT_PARAMETERS = {"ACL": "public-read", 'CacheControl': 'max-age=86400',}
AWS_SECRET_ACCESS_KEY = "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"
AWS_STORAGE_BUCKET_NAME = "acemaven"
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

