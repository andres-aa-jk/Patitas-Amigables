from django.conf import settings
from rest_framework import serializers

from .imagenes import calcular_hash, optimizar_imagen
from .models import Animal, EntregaAnimal, SolicitudAdopcion, VistaAnimal


def validar_tamano_foto(archivo):
    """Rechaza fotos más pesadas que MAX_FOTO_MB (antes de procesarlas)."""
    limite_mb = getattr(settings, "MAX_FOTO_MB", 10)
    if archivo and archivo.size > limite_mb * 1024 * 1024:
        raise serializers.ValidationError(f"La foto no puede pesar más de {limite_mb} MB.")


class AnimalSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    foto = serializers.FileField(required=False, allow_null=True)
    foto_url = serializers.SerializerMethodField()
    especie_display = serializers.CharField(source="get_especie_display", read_only=True)
    estado_salud_display = serializers.CharField(
        source="get_estado_salud_display", read_only=True
    )
    registrado_por_username = serializers.CharField(
        source="registrado_por.username", read_only=True
    )

    class Meta:
        model = Animal
        fields = (
            "id",
            "nombre",
            "especie",
            "especie_display",
            "raza",
            "edad",
            "estado_salud",
            "estado_salud_display",
            "descripcion",
            "foto",
            "foto_url",
            "latitud",
            "longitud",
            "fecha_registro",
            "registrado_por_username",
            "estado_publicacion",
            "estado_adopcion",
            "motivo_rechazo",
        )
        # La moderación y el ciclo de adopción solo cambian por las acciones
        # del administrador, nunca por edición directa.
        read_only_fields = (
            "id",
            "fecha_registro",
            "registrado_por_username",
            "estado_publicacion",
            "estado_adopcion",
            "motivo_rechazo",
        )

    def get_foto_url(self, obj):
        if not obj.foto:
            return None
        request = self.context.get("request")
        url = obj.foto.url
        return request.build_absolute_uri(url) if request else url

    def validate_edad(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("La edad no puede ser negativa.")
        return value

    def validate_foto(self, value):
        validar_tamano_foto(value)
        if value and not calcular_hash(value):
            raise serializers.ValidationError("El archivo no es una imagen válida.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["registrado_por"] = user
        foto = validated_data.get("foto")
        if foto:
            validated_data["foto_hash"] = calcular_hash(foto)
            validated_data["foto"] = optimizar_imagen(foto)
        # Los administradores publican directamente; el resto pasa por revisión.
        if user.es_admin:
            validated_data["estado_publicacion"] = Animal.PUB_APROBADO
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        foto = validated_data.get("foto")
        if foto:
            validated_data["foto_hash"] = calcular_hash(foto)
            validated_data["foto"] = optimizar_imagen(foto)
        if not user.es_admin:
            # Cualquier cambio de un no admin vuelve a revisión.
            instance.estado_publicacion = Animal.PUB_PENDIENTE
            instance.motivo_rechazo = ""
        return super().update(instance, validated_data)


class AnimalAdminSerializer(AnimalSerializer):
    """Vista para el administrador: añade los posibles duplicados."""

    posibles_duplicados = serializers.SerializerMethodField()

    class Meta(AnimalSerializer.Meta):
        fields = AnimalSerializer.Meta.fields + ("posibles_duplicados",)

    def get_posibles_duplicados(self, obj):
        return self.context.get("duplicados", {}).get(str(obj.pk), [])


class SolicitudSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    animal = serializers.CharField(read_only=True)
    animal_id = serializers.CharField(write_only=True)
    animal_nombre = serializers.SerializerMethodField()
    solicitante_username = serializers.CharField(
        source="solicitante.username", read_only=True
    )
    entrega_id = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudAdopcion
        fields = (
            "id", "animal", "animal_id", "animal_nombre", "solicitante_username",
            "motivo", "tipo_vivienda", "tiene_otras_mascotas", "experiencia",
            "acepta_visita", "estado", "observaciones_admin", "fecha",
            "fecha_revision", "entrega_id",
        )
        read_only_fields = ("estado", "observaciones_admin", "fecha", "fecha_revision")

    def get_animal_nombre(self, obj):
        return obj.animal.nombre or f"{obj.animal.get_especie_display()} sin nombre"

    def get_entrega_id(self, obj):
        precargadas = self.context.get("entregas_por_solicitud")
        if precargadas is not None:  # listado: ya viene calculado, sin consulta extra
            return precargadas.get(obj.pk)
        e = obj.entregas.exclude(estado=EntregaAnimal.RECHAZADA).first()
        return str(e.pk) if e else None

    def validate_motivo(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Cuéntanos con al menos 20 caracteres por qué quieres adoptar."
            )
        return value

    def validate_acepta_visita(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "Debes aceptar una visita de verificación del refugio."
            )
        return value


class EntregaSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    solicitud = serializers.CharField()
    animal = serializers.CharField(read_only=True)
    animal_nombre = serializers.SerializerMethodField()
    adoptante_username = serializers.CharField(source="adoptante.username", read_only=True)
    foto = serializers.ImageField(write_only=True)
    foto_repetida = serializers.SerializerMethodField()

    class Meta:
        model = EntregaAnimal
        fields = (
            "id", "solicitud", "animal", "animal_nombre", "adoptante_username",
            "foto", "consentimiento_imagen", "latitud", "longitud", "fecha",
            "confirmada_por_refugio", "fecha_confirmacion_refugio", "estado",
            "observaciones_admin", "fecha_validacion", "foto_repetida",
        )
        read_only_fields = (
            "fecha", "confirmada_por_refugio", "fecha_confirmacion_refugio", "estado",
            "observaciones_admin", "fecha_validacion",
        )

    def get_animal_nombre(self, obj):
        return obj.animal.nombre or f"{obj.animal.get_especie_display()} sin nombre"

    def get_foto_repetida(self, obj):
        request = self.context.get("request")
        if not (request and request.user.is_authenticated and request.user.es_admin):
            return None
        return self.context.get("repetidas", {}).get(str(obj.pk), [])

    def validate_consentimiento_imagen(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "Debes autorizar el tratamiento de la imagen (Ley 1581 de 2012)."
            )
        return value

    def validate_foto(self, value):
        validar_tamano_foto(value)
        if not calcular_hash(value):
            raise serializers.ValidationError("El archivo no es una imagen válida.")
        return value


class VistaSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)
    animal_id = serializers.CharField(read_only=True)
    animal_nombre = serializers.SerializerMethodField()

    class Meta:
        model = VistaAnimal
        fields = (
            "id", "usuario_username", "animal_id", "animal_nombre",
            "inicio", "fin", "duracion_segundos",
        )

    def get_animal_nombre(self, obj):
        return obj.animal.nombre or f"{obj.animal.get_especie_display()} sin nombre"