"""python manage.py probar_conexion  ->  comprueba la conexión con MongoDB y explica fallos comunes."""
import re

from django.core.management.base import BaseCommand
from django.db import connection


def ocultar_credenciales(uri):
    """mongodb+srv://usuario:clave@host -> mongodb+srv://***:***@host (nunca se imprimen las claves)."""
    return re.sub(r"//[^@/]+@", "//***:***@", uri or "")


class Command(BaseCommand):
    help = "Comprueba la conexión con MongoDB (local o Atlas) y sugiere la causa probable si falla."

    def handle(self, *args, **options):
        from pymongo.errors import ConfigurationError, OperationFailure, ServerSelectionTimeoutError

        ajustes = connection.settings_dict
        uri = ajustes.get("HOST") or ""
        self.stdout.write(f"Servidor:       {ocultar_credenciales(uri)}")
        self.stdout.write(f"Base de datos:  {ajustes.get('NAME')}")

        if uri.startswith("mongodb+srv://") and "serverSelectionTimeoutMS" not in uri:
            self.stdout.write(self.style.WARNING(
                "Consejo: añade &serverSelectionTimeoutMS=5000 al final de MONGODB_URI para que un fallo "
                "de red se note en 5 segundos y no en 30."
            ))

        try:
            connection.database.command("ping")
            colecciones = connection.database.list_collection_names()
        except ServerSelectionTimeoutError as e:
            mensaje = str(e)
            self.stderr.write(self.style.ERROR("No se pudo llegar al servidor."))
            if "SSL" in mensaje or "TLS" in mensaje or "handshake" in mensaje:
                self.stderr.write(
                    "Causa más probable: Atlas rechaza tu IP. Ve a Atlas -> Security -> Network Access y "
                    "añade tu IP actual (o 0.0.0.0/0 solo para desarrollo). Otras causas: VPN/antivirus que "
                    "intercepta TLS, o una red que bloquea el puerto 27017."
                )
            else:
                self.stderr.write(
                    "Revisa que el servidor esté encendido (MongoDB local) o que el clúster no esté pausado "
                    "(Atlas), y que tengas internet."
                )
            return
        except OperationFailure as e:
            if getattr(e, "code", None) == 18 or "auth" in str(e).lower():
                self.stderr.write(self.style.ERROR(
                    "Usuario o contraseña incorrectos. Si la contraseña tiene caracteres especiales "
                    "(@ : / ? # %) hay que codificarlos en la URI (p. ej. @ -> %40)."
                ))
            else:
                self.stderr.write(self.style.ERROR(f"MongoDB respondió con un error: {type(e).__name__}."))
            return
        except ConfigurationError:
            self.stderr.write(self.style.ERROR(
                "La URI no se pudo interpretar o el DNS no resolvió el clúster. Revisa MONGODB_URI "
                "(host copiado de Atlas -> Connect) y tu conexión a internet."
            ))
            return
        except Exception as e:  # noqa: BLE001
            self.stderr.write(self.style.ERROR(f"Error inesperado: {type(e).__name__}."))
            return

        self.stdout.write(self.style.SUCCESS(f"Conexión correcta. Colecciones en la base: {len(colecciones)}"))
