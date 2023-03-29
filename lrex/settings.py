import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CONFIG_DIR)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
DEV = True

ALLOWED_HOSTS = []


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
    'crispy_bootstrap5',

    'django.contrib.admin',
]

MIDDLEWARE = [
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
        'DIRS': ['lrex/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.home.context_processors.announcements',
            ],
        },
    },
]

WSGI_APPLICATION = 'lrex.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Auth
LOGIN_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

ACCOUNT_ACTIVATION_DAYS = 7


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


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(CONFIG_DIR, 'assets'),
    os.path.join(CONFIG_DIR, 'static'),
]

# Other
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Security (set all True in production)
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '&+b$6n1(x=h0($ww_d4^j&6r%rtv47$gacl!nazl71g7&siqa3'

# server settings
SITE_ID = 1
ADMINS = [('Support', 'support@l-rex.de')]
DEFAULT_FROM_EMAIL = 'support@l-rex.de'

# lrex
LREX_VERSION = "1.0.3"
LREX_CONTACT_MD = 'Please define contact as markdown in local.py'
LREX_PRIVACY_MD = 'Please define privacy statement as markdown in local.py'
LREX_RECIPIENT = ''
LREX_IBAN = ''
LREX_BIC = ''
LREX_ANNOUNCEMENTS = []

# Import local settings
try:
    from .local import *
except ImportError:
    pass
