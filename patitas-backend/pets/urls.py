from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnimalViewSet, EntregaViewSet, SolicitudViewSet, VistaViewSet

router = DefaultRouter()
router.register(r"animales", AnimalViewSet, basename="animal")
router.register(r"solicitudes", SolicitudViewSet, basename="solicitud")
router.register(r"entregas", EntregaViewSet, basename="entrega")
router.register(r"vistas", VistaViewSet, basename="vista")

urlpatterns = [
    path("", include(router.urls)),
]
