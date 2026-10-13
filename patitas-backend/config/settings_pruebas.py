"""Configuración SOLO para pruebas en entorno sin MongoDB: usa SQLite.
El resto de la configuración (JWT, DRF, CORS, modelos) es la del proyecto."""
import sys, types
from django.db import models as _m
# Sustituto de django_mongodb_backend (no hay MongoDB en este entorno): ObjectIdAutoField -> BigAutoField
_pkg = types.ModuleType("django_mongodb_backend"); _f = types.ModuleType("django_mongodb_backend.fields")
_f.ObjectIdAutoField = _m.BigAutoField; _pkg.fields = _f
sys.modules.setdefault("django_mongodb_backend", _pkg); sys.modules.setdefault("django_mongodb_backend.fields", _f)

from .settings import *  # noqa

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "pruebas_db.sqlite3"}}
DATABASE_ROUTERS = []
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MEDIA_ROOT = BASE_DIR / "media_pruebas"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # solo para acelerar pruebas
ALLOWED_HOSTS = ["*"]
MIGRATION_MODULES = {"users": "pruebas.mig_users", "pets": "pruebas.mig_pets"}

PRIVATE_MEDIA_ROOT = BASE_DIR / "media_privado_pruebas"
