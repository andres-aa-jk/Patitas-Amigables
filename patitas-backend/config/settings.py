"""
Configuración de Django para el backend de Patitas Amigables.
Base de datos: MongoDB (vía django-mongodb-backend).
"""
from pathlib import Path
from datetime import timedelta
import os
import sys

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")
# Seguro por defecto: el modo de depuración hay que pedirlo (DEBUG=True en el .env local).
DEBUG = os.getenv("DEBUG", "False") == "True"
TESTING = "test" in sys.argv
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# Sin DEBUG, el servidor se niega a arrancar con una clave de ejemplo o demasiado corta.
_CLAVES_DE_EJEMPLO = {"cambia-esto-en-produccion", "pon-aqui-una-clave-larga-y-secreta"}
if not DEBUG and not TESTING and (SECRET_KEY in _CLAVES_DE_EJEMPLO or len(SECRET_KEY) < 32):
    raise ImproperlyConfigured(
        "SECRET_KEY insegura. Define en el .env una clave aleatoria de al menos 32 caracteres "
        "(o DEBUG=True solo en tu equipo de desarrollo). Para generar una: "
        "python -c \"from django.core.management.utils import get_random_secret_key as g; print(g())\""
    )

# Tamaño máximo de las fotos subidas (MB). Después se redimensionan al guardarlas.
MAX_FOTO_MB = int(os.getenv("MAX_FOTO_MB", "10"))

INSTALLED_APPS = [
    "config.apps.MongoAdminConfig",          # en vez de 'django.contrib.admin'
    "config.apps.MongoAuthConfig",           # en vez de 'django.contrib.auth'
    "config.apps.MongoContentTypesConfig",   # en vez de 'django.contrib.contenttypes'
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "pets",
    "users",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# BASE DE DATOS: MongoDB
# ---------------------------------------------------------------------------
# MONGODB_URI ejemplo Atlas:
#   mongodb+srv://usuario:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
# MONGODB_URI ejemplo local:
#   mongodb://localhost:27017
DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "HOST": os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        "NAME": os.getenv("MONGODB_NAME", "patitas_amigables"),
    }
}

# Necesario para que Mongo no cree colecciones de modelos embebidos
DATABASE_ROUTERS = ["django_mongodb_backend.routers.MongoRouter"]

# Mongo usa ObjectId como clave primaria por defecto
DEFAULT_AUTO_FIELD = 'django_mongodb_backend.fields.ObjectIdAutoField'

# Modelo de usuario personalizado
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
# Fotos de entrega: almacenamiento privado, nunca servido por /media/.
PRIVATE_MEDIA_ROOT = BASE_DIR / "media_privado"

# ---------------------------------------------------------------------------
# Django REST Framework + JWT
# ---------------------------------------------------------------------------
# Tasas por usuario/IP. En las pruebas automáticas se desactivan para no falsear resultados.
THROTTLE_RATES = {
    "anon": "200/min",      # visitantes sin sesión (por IP)
    "user": "600/min",      # usuarios con sesión
    "login": "10/min",      # intentos de inicio de sesión
    "registro": "5/hour",   # registros nuevos
    "subida": "30/hour",    # crear animales, solicitudes o constancias
}
if TESTING:
    THROTTLE_RATES = {k: "100000/min" for k in THROTTLE_RATES}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        ("rest_framework.renderers.JSONRenderer", "rest_framework.renderers.BrowsableAPIRenderer")
        if DEBUG
        else ("rest_framework.renderers.JSONRenderer",)
    ),
    # Límite de peticiones: frena la fuerza bruta y el abuso (429 al excederlo).
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": THROTTLE_RATES,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),  # el frontend renueva con el refresh token
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------------------------------------------------------------------------
# CORS: permitir que el React (Vite) consuma la API
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

CORS_ALLOW_CREDENTIALS = True

MIGRATION_MODULES = {
    "admin": "mongo_migrations.admin",
    "auth": "mongo_migrations.auth",
    "contenttypes": "mongo_migrations.contenttypes",
}

# ---------------------------------------------------------------------------
# Seguridad en producción (solo con DEBUG=False)
# ---------------------------------------------------------------------------
if not DEBUG and not TESTING:
    FORZAR_HTTPS = os.getenv("FORZAR_HTTPS", "True") == "True"
    SECURE_SSL_REDIRECT = FORZAR_HTTPS
    SESSION_COOKIE_SECURE = FORZAR_HTTPS
    CSRF_COOKIE_SECURE = FORZAR_HTTPS
    # HSTS empieza corto (1 hora); súbelo (p. ej. 31536000) cuando HTTPS esté probado.
    SECURE_HSTS_SECONDS = int(os.getenv("HSTS_SEGUNDOS", "3600")) if FORZAR_HTTPS else 0
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    if os.getenv("DETRAS_DE_PROXY", "False") == "True":  # nginx, Render, Railway, etc.
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Registro de actividad (consola). Los intentos de login fallidos van a 'patitas.seguridad'.
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"}},
    "handlers": {"consola": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["consola"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
