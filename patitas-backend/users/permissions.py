from rest_framework import permissions


class IsAdminRol(permissions.BasePermission):
    """Solo usuarios con rol de administrador (o superusuarios)."""

    message = "Solo los administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.es_admin)
