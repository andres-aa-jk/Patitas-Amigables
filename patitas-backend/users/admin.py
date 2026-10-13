from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "numero", "rol", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Datos de contacto", {"fields": ("direccion", "numero")}),
        ("Rol y consentimiento", {"fields": ("rol", "acepta_politica", "fecha_aceptacion")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Datos de contacto", {"fields": ("email", "direccion", "numero", "rol")}),
    )
