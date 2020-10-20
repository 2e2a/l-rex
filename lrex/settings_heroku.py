import django_heroku

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CONFIG_DIR)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'
DEV = False

ALLOWED_HOSTS = [
    'l-rex.herokuapp.com',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'apps.contrib.apps.ContribConfig',
    'apps.user.apps.UserConfig',
    'apps.home.apps.HomeConfig',
    'apps.study.apps.StudyConfig',
    'apps.materials.apps.MaterialsConfig',
    'apps.item.apps.ItemConfig',
    'apps.trial.apps.TrialConfig',

    'markdownx',
    'crispy_forms',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    'django.contrib.admin',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lrex.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'lrex.wsgi.application'

# Auth
LOGIN_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_FORMS = {'signup': 'apps.home.forms.FixedAutofocusSignupForm'}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
# https://devcenter.heroku.com/articles/django-assets/

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(CONFIG_DIR, 'assets'),
    os.path.join(CONFIG_DIR, 'static'),
]


# Other
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Security (set all True in production)
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# server settings
SITE_ID = 1
ADMINS = []
DEFAULT_FROM_EMAIL = 'lrex@localhost'

# lrex
LREX_VERSION = 0
LREX_CONTACT_MD = 'Please define contact as markdown in local.py'
LREX_PRIVACY_MD = 'Please define privacy statement as markdown in local.py'


# Activate Django-Heroku.
django_heroku.settings(locals())
