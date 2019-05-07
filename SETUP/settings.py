"""
Django settings for fm_eventmanager project.

Generated by 'django-admin startproject' using Django 1.9.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#4jb6($!lns7dm@0$%80q&sk2_d7(qy*f^$ky!4z@1c-gonv8_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
	'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
	},
    'filters' : {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers' : {
        'console' : {
            'level' : 'DEBUG',
            'filters': ['require_debug_true'],
            'formatter' : 'verbose',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console',],
            'level' : 'DEBUG' if DEBUG else 'INFO',
        },      
        'registration': {
            'level' : 'DEBUG' if DEBUG else 'INFO',
            'propagate' : True,
        },
    }
}


ADMINS = [('Dustin Hickman', 'dustin.hickman@animeusa.org'),]
SERVER_EMAIL = "ausa_it@animeusa.org"

ALLOWED_HOSTS = ['45.33.125.163','http://regtest.animeusa.org/']


# Application definition

INSTALLED_APPS = [
    'flat_responsive',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'widget_tweaks',
    'mathfilters',
    'nested_inline',
    'events.apps.EventsConfig',
    'import_export',
    'django_extensions',
    'django_u2f',
    'argonauts',
    'registration',
    'volunteer.apps.VolunteerConfig',
    'debug_toolbar',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'fm_eventmanager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
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

WSGI_APPLICATION = 'fm_eventmanager.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE' : 'django.db.backends.sqlite3',
        'NAME' : os.path.join(BASE_DIR, 'db.sqlite3'), 
        'TEST' : {
            'NAME' : os.path.join(BASE_DIR, 'test-db.sqlite3'),
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

#AUTH_PASSWORD_VALIDATORS = [
#    {
#        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#    },
#    {
#        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#    },
#    {
#        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#    },
#    {
#        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#    },
#]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1

LOGIN_REDIRECT_URL = 'u2f:two-factor-settings'
LOGIN_URL = 'u2f:login'

INTERNAL_IPS = ['127.0.0.1']

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
# STATIC_ROOT = '/root/projects/furthemore/static/'

# Session Management
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60*60  # 1hr

# Default email to display as part of error messages
APIS_DEFAULT_EMAIL = "registration@example.com"
APIS_DEALER_HEAD = "marketplace@example.com"
APIS_STAFF_HEAD = "staff@example.com"

# Sandbox values - DO NOT check in production ids
AUTHNET_NAME = '426rwVfr3G47'
AUTHNET_TRANSACTIONKEY = '399UTfznCV7gz224'

# Sandbox values = DO NOT check in production ids
SQUARE_APPLICATION_ID = 'sandbox-sq0idp-1a_xxxxxxxxxxxxxxxxxxx'
SQUARE_ACCESS_TOKEN = 'sandbox-sq0atb-xxxxxxxxxxxxxxxxxxxxxx'
SQUARE_LOCATION_ID = 'xxxxxxxxx...'
SQUARE_CURRENCY = 'USD'

# Sandbox values - DO NOT check in production credentials
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'dustin.hickman@animeusa.org'
EMAIL_HOST_PASSWORD = 'Notekittens4!'
EMAIL_PORT = 587

# Return channel for Android register application
REGISTER_KEY = 'df14e4d5469e801dbc8e1df4eebd97b3'

# Print handler for cash drawer and receipts
REGISTER_PRINTER_URI = 'https://print.example.com:5000'

# Firebase/Pushy.me cloud-push API key
CLOUD_MESSAGING_KEY = "AAA..."

# USE AN ENV VARIABLE IN PROD.
# http://45.33.125.163/api/pull/
GITHUB_WEBHOOK_KEY = '5qhMSxw321fRjwIApgB6xIlibBaQPe1fI6thm972EStBSIH0g4'