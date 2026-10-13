from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models


def almacenamiento_privado():
    """Las fotos de entrega no se sirven públicamente (contienen datos personales)."""
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)


class Animal(models.Model):
    ESPECIE_CHOICES = [
        ("perro", "Perro"),
        ("gato", "Gato"),
        ("conejo", "Conejo"),
        ("ave", "Ave"),
    ]

    ESTADO_SALUD_CHOICES = [
        ("saludable", "Saludable"),
        ("lesionado", "Lesionado"),
        ("enfermo", "Enfermo"),
        ("desnutrido", "Desnutrido"),
    ]

    PUB_PENDIENTE = "pendiente"
    PUB_APROBADO = "aprobado"
    PUB_RECHAZADO = "rechazado"
    PUBLICACION_CHOICES = [
        (PUB_PENDIENTE, "Pendiente de revisión"),
        (PUB_APROBADO, "Aprobado"),
        (PUB_RECHAZADO, "Rechazado"),
    ]

    ADOP_DISPONIBLE = "disponible"
    ADOP_EN_ENTREGA = "en_entrega"
    ADOP_ADOPTADO = "adoptado"
    ADOPCION_CHOICES = [
        (ADOP_DISPONIBLE, "Disponible"),
        (ADOP_EN_ENTREGA, "En entrega"),
        (ADOP_ADOPTADO, "Adoptado"),
    ]

    nombre = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Nombre"
    )
    especie = models.CharField(
        max_length=20, choices=ESPECIE_CHOICES, verbose_name="Especie"
    )
    raza = models.CharField(max_length=50, blank=True, null=True, verbose_name="Raza")
    edad = models.IntegerField(blank=True, null=True, verbose_name="Edad")
    estado_salud = models.CharField(
        max_length=20, choices=ESTADO_SALUD_CHOICES, verbose_name="Estado de salud"
    )
    descripcion = models.TextField(verbose_name="Descripción")
    foto = models.FileField(
        upload_to="animales/", verbose_name="Foto", blank=True, null=True
    )
    # Huella perceptual de la foto (dHash) para detectar duplicados.
    foto_hash = models.CharField(max_length=16, blank=True, default="")

    # En MongoDB se usan floats en lugar de Decimal: es más simple y permite
    # índices geoespaciales más adelante.
    latitud = models.FloatField(verbose_name="Latitud")
    longitud = models.FloatField(verbose_name="Longitud")

    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de registro"
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="animales",
        verbose_name="Registrado por",
    )

    # Moderación: un animal solo es público cuando un administrador lo aprueba.
    estado_publicacion = models.CharField(
        max_length=10, choices=PUBLICACION_CHOICES, default=PUB_PENDIENTE
    )
    motivo_rechazo = models.TextField(blank=True, default="")
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="animales_revisados",
    )
    fecha_revision = models.DateTimeField(null=True, blank=True)

    # Ciclo de adopción.
    estado_adopcion = models.CharField(
        max_length=12, choices=ADOPCION_CHOICES, default=ADOP_DISPONIBLE
    )

    class Meta:
        verbose_name = "Animal"
        verbose_name_plural = "Animales"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.especie} - {self.nombre or 'Sin nombre'}"


class SolicitudAdopcion(models.Model):
    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    ESTADO_CHOICES = [
        (PENDIENTE, "Pendiente"),
        (APROBADA, "Aprobada"),
        (RECHAZADA, "Rechazada"),
    ]

    animal = models.ForeignKey(
        Animal, on_delete=models.CASCADE, related_name="solicitudes"
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="solicitudes"
    )
    motivo = models.TextField(verbose_name="Motivo de la adopción")
    tipo_vivienda = models.CharField(max_length=60)
    tiene_otras_mascotas = models.BooleanField(default=False)
    experiencia = models.TextField(blank=True, default="")
    acepta_visita = models.BooleanField(default=False)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=PENDIENTE)
    observaciones_admin = models.TextField(blank=True, default="")
    fecha = models.DateTimeField(auto_now_add=True)
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_revisadas",
    )
    fecha_revision = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Solicitud de {self.solicitante_id} por {self.animal_id} ({self.estado})"


class EntregaAnimal(models.Model):
    """Constancia fotográfica de quién recogió al animal."""

    PENDIENTE = "pendiente"
    VALIDADA = "validada"
    RECHAZADA = "rechazada"
    ESTADO_CHOICES = [
        (PENDIENTE, "Pendiente de validación"),
        (VALIDADA, "Validada"),
        (RECHAZADA, "Rechazada"),
    ]

    solicitud = models.ForeignKey(
        SolicitudAdopcion, on_delete=models.CASCADE, related_name="entregas"
    )
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="entregas")
    adoptante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="entregas"
    )
    foto = models.FileField(upload_to="entregas/", storage=almacenamiento_privado)
    foto_hash = models.CharField(max_length=16, blank=True, default="")
    consentimiento_imagen = models.BooleanField(default=False)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    confirmada_por_refugio = models.BooleanField(default=False)
    fecha_confirmacion_refugio = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=PENDIENTE)
    observaciones_admin = models.TextField(blank=True, default="")
    validada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entregas_validadas",
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha"]


class VistaAnimal(models.Model):
    """Registro de cuándo y por cuánto tiempo un usuario consultó la ficha de un animal."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vistas"
    )
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="vistas")
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    duracion_segundos = models.IntegerField(default=0)

    class Meta:
        ordering = ["-inicio"]
