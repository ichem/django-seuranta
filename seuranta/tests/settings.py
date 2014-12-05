import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = '27=y9odjqrshzyu%c3fr26znrpo(@j#1dcrs2-_ax_9rr3n3yf'

DEBUG = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'timezone_field',
    'globetrotting',

    'userena'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'userena.backends.UserenaAuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
)
ANONYMOUS_USER_ID = -1
AUTH_PROFILE_MODULE = 'seuranta.UserProfile'
LOGIN_REDIRECT_URL = '/accounts/%(username)s/'
LOGIN_URL = '/accounts/signin/'
LOGOUT_URL = '/accounts/signout/'

USERENA_ACTIVATION_REQUIRED = False
USERENA_SIGNIN_AFTER_SIGNUP = True
USERENA_FORBIDDEN_USERNAMES = (
    'tracker',
    'dashboard',
    'api',
    'accounts',
    'admin',
    'signup',
    'signout',
    'signin',
    'activate',
    'me',
    'password'
)
USERENA_DISABLE_PROFILE_LIST = True
USERENA_USE_MESSAGES = False
USERENA_WITHOUT_USERNAMES = True
USERENA_HIDE_EMAIL = True

ROOT_URLCONF = 'seuranta.tests.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

LANGUAGE_CODE = 'en-en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DATETIME_FORMAT = 'r'

STATIC_URL = '/static/'

SITE_ID = 1
