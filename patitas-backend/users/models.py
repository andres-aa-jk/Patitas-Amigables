from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario personalizado con dirección y teléfono (igual que el proyecto original)."""

    direccion = models.TextField(verbose_name="Dirección", blank=True, default="")
    numero = models.CharField(
        max_length=20, verbose_name="Número de teléfono", blank=True, default=""
    )

    ROL_USUARIO = "usuario"
    ROL_ADMIN = "admin"
    ROL_CHOICES = [(ROL_USUARIO, "Usuario"), (ROL_ADMIN, "Administrador")]

    rol = models.CharField(
        max_length=10, choices=ROL_CHOICES, default=ROL_USUARIO, verbose_name="Rol"
    )
    # Ley 1581 de 2012: autorización expresa para el tratamiento de datos.
    acepta_politica = models.BooleanField(
        default=False, verbose_name="Acepta la política de tratamiento de datos"
    )
    fecha_aceptacion = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de aceptación de la política"
    )

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    @property
    def es_admin(self):
        return self.rol == self.ROL_ADMIN or self.is_superuser

    def __str__(self):
        return self.username
