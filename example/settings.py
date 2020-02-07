import os

from django import VERSION

PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(PROJECT_ROOT, "example.db"),
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
        "TEST": {"NAME": ":memory:", "ENGINE": "django.db.backends.sqlite3",},
    }
}

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache",}}

TIME_ZONE = "America/Chicago"

LANGUAGE_CODE = "en-us"

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/media/"

# Don't share this with anybody.
SECRET_KEY = "ljlv2lb2d&)#by6th=!v=03-c^(o4lop92i@z4b3f1&ve0yx6d"

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # 'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

INTERNAL_IPS = ("127.0.0.1",)


TEMPLATE_CONTEXT_PROCESSORS = ()

ROOT_URLCONF = "example.urls"

SITE_ID = 1

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.flatpages",
    "django.contrib.messages",
    "django.contrib.admin",
    "authority",
    "example.exampleapp",
)

if VERSION >= (1, 5):
    INSTALLED_APPS = INSTALLED_APPS + ("example.users",)
    AUTH_USER_MODEL = "users.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # insert your TEMPLATE_DIRS here
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
