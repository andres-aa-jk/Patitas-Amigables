from django.contrib import admin

from .models import Animal, EntregaAnimal, SolicitudAdopcion, VistaAnimal


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "especie", "estado_salud", "estado_publicacion",
                    "estado_adopcion", "fecha_registro", "registrado_por")
    list_filter = ("especie", "estado_salud", "estado_publicacion", "estado_adopcion")
    search_fields = ("nombre", "raza", "descripcion")


@admin.register(SolicitudAdopcion)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ("animal", "solicitante", "estado", "fecha")
    list_filter = ("estado",)


@admin.register(EntregaAnimal)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ("animal", "adoptante", "estado", "confirmada_por_refugio", "fecha")
    list_filter = ("estado",)


@admin.register(VistaAnimal)
class VistaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "animal", "inicio", "duracion_segundos")
