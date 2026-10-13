import math

from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from users.permissions import IsAdminRol

from .imagenes import UMBRAL_DUPLICADO, distancia
from .models import Animal, EntregaAnimal, SolicitudAdopcion, VistaAnimal
from .serializers import (
    AnimalAdminSerializer,
    AnimalSerializer,
    EntregaSerializer,
    SolicitudSerializer,
    VistaSerializer,
)

# Tope de una visualización: evita contar pestañas olvidadas abiertas.
MAX_SEGUNDOS_VISTA = 30 * 60


def distancia_metros(lat1, lon1, lat2, lon2):
    """Fórmula de Haversine: distancia en metros entre dos coordenadas."""
    R = 6378137.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Solo quien registró el animal (o un administrador) puede editarlo o borrarlo."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.es_admin or obj.registrado_por_id == request.user.id


def animales_visibles(user):
    """Público: aprobados y disponibles. Dueño: además los suyos. Admin: todos."""
    if user.is_authenticated and user.es_admin:
        return Animal.objects.all()
    publico = Q(estado_publicacion=Animal.PUB_APROBADO, estado_adopcion=Animal.ADOP_DISPONIBLE)
    if user.is_authenticated:
        return Animal.objects.filter(publico | Q(registrado_por=user))
    return Animal.objects.filter(publico)


def duplicados_de(animales):
    """{id_animal: [{id, nombre, distancia}]} comparando huellas de imagen (dHash)."""
    con_hash = [a for a in Animal.objects.all() if a.foto_hash]
    resultado = {}
    for a in animales:
        if not a.foto_hash:
            continue
        similares = []
        for o in con_hash:
            if o.pk == a.pk:
                continue
            d = distancia(a.foto_hash, o.foto_hash)
            if d <= UMBRAL_DUPLICADO:
                similares.append({"id": str(o.pk), "nombre": o.nombre or "Sin nombre",
                                  "distancia": d, "estado_publicacion": o.estado_publicacion})
        if similares:
            resultado[str(a.pk)] = sorted(similares, key=lambda x: x["distancia"])
    return resultado


class AnimalViewSet(viewsets.ModelViewSet):
    """
    GET    /api/animales/                 -> lista (solo aprobados y disponibles)
    POST   /api/animales/                 -> crear (queda pendiente de revisión)
    GET    /api/animales/<id>/            -> detalle
    PATCH  /api/animales/<id>/            -> editar (dueño o admin)
    DELETE /api/animales/<id>/            -> borrar (dueño o admin)
    GET    /api/animales/cercanos/?lat=&lng=&radio=1000
    GET    /api/animales/mis-animales/    -> los del usuario autenticado
    GET    /api/animales/pendientes/      -> (admin) cola de revisión con posibles duplicados
    POST   /api/animales/<id>/revisar/    -> (admin) {decision: aprobar|rechazar, motivo}
    """

    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = animales_visibles(self.request.user).select_related("registrado_por")
        especie = self.request.query_params.get("especie")
        if especie:
            qs = qs.filter(especie=especie)
        estado = self.request.query_params.get("estado_salud")
        if estado:
            qs = qs.filter(estado_salud=estado)
        return qs

    @action(detail=False, methods=["get"], url_path="cercanos")
    def cercanos(self, request):
        try:
            lat = float(request.query_params.get("lat"))
            lng = float(request.query_params.get("lng"))
        except (TypeError, ValueError):
            return Response(
                {"detail": "Debes enviar los parámetros lat y lng."}, status=400
            )

        radio = float(request.query_params.get("radio", 1000))
        cercanos = [
            a
            for a in self.get_queryset()
            if distancia_metros(lat, lng, a.latitud, a.longitud) <= radio
        ]
        serializer = self.get_serializer(cercanos, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="mis-animales",
        permission_classes=[permissions.IsAuthenticated],
    )
    def mis_animales(self, request):
        qs = Animal.objects.filter(registrado_por=request.user)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="pendientes", permission_classes=[IsAdminRol])
    def pendientes(self, request):
        estado = request.query_params.get("estado", Animal.PUB_PENDIENTE)
        qs = list(Animal.objects.filter(estado_publicacion=estado).select_related("registrado_por"))
        ctx = {**self.get_serializer_context(), "duplicados": duplicados_de(qs)}
        return Response(AnimalAdminSerializer(qs, many=True, context=ctx).data)

    @action(detail=True, methods=["post"], url_path="revisar", permission_classes=[IsAdminRol])
    def revisar(self, request, pk=None):
        animal = self.get_object()
        decision = request.data.get("decision")
        if decision not in ("aprobar", "rechazar"):
            return Response({"decision": "Debe ser 'aprobar' o 'rechazar'."}, status=400)
        motivo = (request.data.get("motivo") or "").strip()
        if decision == "rechazar" and not motivo:
            return Response({"motivo": "Indica el motivo del rechazo."}, status=400)
        animal.estado_publicacion = (
            Animal.PUB_APROBADO if decision == "aprobar" else Animal.PUB_RECHAZADO
        )
        animal.motivo_rechazo = motivo if decision == "rechazar" else ""
        animal.revisado_por = request.user
        animal.fecha_revision = timezone.now()
        animal.save()
        return Response(self.get_serializer(animal).data)


class SolicitudViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                       mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    POST /api/solicitudes/                   -> pedir la adopción de un animal
    GET  /api/solicitudes/                   -> las propias (el admin ve todas; ?estado=)
    POST /api/solicitudes/<id>/revisar/      -> (admin) {decision: aprobar|rechazar, observaciones}
    """

    serializer_class = SolicitudSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        qs = SolicitudAdopcion.objects.select_related("animal", "solicitante")
        if not u.es_admin:
            qs = qs.filter(solicitante=u)
        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        animal = get_object_or_404(
            Animal.objects.filter(
                estado_publicacion=Animal.PUB_APROBADO, estado_adopcion=Animal.ADOP_DISPONIBLE
            ),
            pk=ser.validated_data["animal_id"],
        )
        if animal.registrado_por_id == request.user.id:
            return Response({"detail": "No puedes adoptar un animal que tú registraste."}, status=400)
        if SolicitudAdopcion.objects.filter(
            animal=animal, solicitante=request.user, estado=SolicitudAdopcion.PENDIENTE
        ).exists():
            return Response({"detail": "Ya tienes una solicitud pendiente para este animal."}, status=400)
        datos = {k: v for k, v in ser.validated_data.items() if k != "animal_id"}
        sol = SolicitudAdopcion.objects.create(animal=animal, solicitante=request.user, **datos)
        return Response(self.get_serializer(sol).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="revisar", permission_classes=[IsAdminRol])
    def revisar(self, request, pk=None):
        sol = self.get_object()
        decision = request.data.get("decision")
        if decision not in ("aprobar", "rechazar"):
            return Response({"decision": "Debe ser 'aprobar' o 'rechazar'."}, status=400)
        if sol.estado != SolicitudAdopcion.PENDIENTE:
            return Response({"detail": "La solicitud ya fue revisada."}, status=400)
        obs = (request.data.get("observaciones") or "").strip()
        if decision == "rechazar" and not obs:
            return Response({"observaciones": "Indica el motivo del rechazo."}, status=400)
        ahora = timezone.now()
        if decision == "aprobar":
            if sol.animal.estado_adopcion != Animal.ADOP_DISPONIBLE:
                return Response({"detail": "El animal ya no está disponible."}, status=400)
            sol.estado = SolicitudAdopcion.APROBADA
            sol.animal.estado_adopcion = Animal.ADOP_EN_ENTREGA
            sol.animal.save()
            # Las demás solicitudes pendientes por el mismo animal se cierran.
            for otra in SolicitudAdopcion.objects.filter(
                animal=sol.animal, estado=SolicitudAdopcion.PENDIENTE
            ).exclude(pk=sol.pk):
                otra.estado = SolicitudAdopcion.RECHAZADA
                otra.observaciones_admin = "El animal fue asignado a otra solicitud."
                otra.revisado_por = request.user
                otra.fecha_revision = ahora
                otra.save()
        else:
            sol.estado = SolicitudAdopcion.RECHAZADA
        sol.observaciones_admin = obs
        sol.revisado_por = request.user
        sol.fecha_revision = ahora
        sol.save()
        return Response(self.get_serializer(sol).data)


class EntregaViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                     mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    POST /api/entregas/                      -> subir la foto de recogida (multipart)
    GET  /api/entregas/                      -> las propias / las de mis animales / todas (admin)
    GET  /api/entregas/<id>/foto/            -> la foto (solo adoptante, refugio dueño o admin)
    POST /api/entregas/<id>/confirmar/       -> el refugio confirma que entregó al animal
    POST /api/entregas/<id>/validar/         -> (admin) {decision: validar|rechazar, observaciones}
    """

    serializer_class = EntregaSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        u = self.request.user
        qs = EntregaAnimal.objects.select_related("animal", "adoptante", "solicitud")
        if not u.es_admin:
            qs = qs.filter(Q(adoptante=u) | Q(animal__registrado_por=u))
        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request and self.request.user.is_authenticated and self.request.user.es_admin:
            ctx["repetidas"] = self._repetidas()
        return ctx

    def _repetidas(self):
        """Entregas cuya foto coincide con otra entrega o con la foto de un animal."""
        entregas = [e for e in EntregaAnimal.objects.all() if e.foto_hash]
        animales = [a for a in Animal.objects.all() if a.foto_hash]
        res = {}
        for e in entregas:
            hits = []
            for o in entregas:
                if o.pk != e.pk and distancia(e.foto_hash, o.foto_hash) <= UMBRAL_DUPLICADO:
                    hits.append({"tipo": "entrega", "id": str(o.pk)})
            for a in animales:
                if distancia(e.foto_hash, a.foto_hash) <= UMBRAL_DUPLICADO:
                    hits.append({"tipo": "animal", "id": str(a.pk), "nombre": a.nombre or "Sin nombre"})
            if hits:
                res[str(e.pk)] = hits
        return res

    def create(self, request, *args, **kwargs):
        from .imagenes import calcular_hash

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sol = get_object_or_404(
            SolicitudAdopcion, pk=ser.validated_data["solicitud"], solicitante=request.user
        )
        if sol.estado != SolicitudAdopcion.APROBADA or sol.animal.estado_adopcion != Animal.ADOP_EN_ENTREGA:
            return Response({"detail": "Solo puedes subir la constancia de una adopción aprobada en entrega."}, status=400)
        if sol.entregas.exclude(estado=EntregaAnimal.RECHAZADA).exists():
            return Response({"detail": "Esta adopción ya tiene una constancia en revisión o validada."}, status=400)
        foto = ser.validated_data["foto"]
        entrega = EntregaAnimal.objects.create(
            solicitud=sol, animal=sol.animal, adoptante=request.user, foto=foto,
            foto_hash=calcular_hash(foto),
            consentimiento_imagen=ser.validated_data["consentimiento_imagen"],
            latitud=ser.validated_data.get("latitud"), longitud=ser.validated_data.get("longitud"),
        )
        return Response(self.get_serializer(entrega).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="foto")
    def foto(self, request, pk=None):
        entrega = self.get_object()  # el queryset ya restringe a las partes y al admin
        if not entrega.foto:
            raise Http404
        return FileResponse(entrega.foto.open("rb"))

    @action(detail=True, methods=["post"], url_path="confirmar")
    def confirmar(self, request, pk=None):
        entrega = self.get_object()
        if entrega.animal.registrado_por_id != request.user.id:
            return Response({"detail": "Solo el refugio que registró el animal puede confirmar."}, status=403)
        entrega.confirmada_por_refugio = True
        entrega.fecha_confirmacion_refugio = timezone.now()
        entrega.save()
        return Response(self.get_serializer(entrega).data)

    @action(detail=True, methods=["post"], url_path="validar", permission_classes=[IsAdminRol])
    def validar(self, request, pk=None):
        entrega = self.get_object()
        decision = request.data.get("decision")
        if decision not in ("validar", "rechazar"):
            return Response({"decision": "Debe ser 'validar' o 'rechazar'."}, status=400)
        if entrega.estado != EntregaAnimal.PENDIENTE:
            return Response({"detail": "La constancia ya fue revisada."}, status=400)
        obs = (request.data.get("observaciones") or "").strip()
        if decision == "rechazar" and not obs:
            return Response({"observaciones": "Indica el motivo del rechazo."}, status=400)
        if decision == "validar":
            entrega.estado = EntregaAnimal.VALIDADA
            entrega.animal.estado_adopcion = Animal.ADOP_ADOPTADO
            entrega.animal.save()
        else:
            entrega.estado = EntregaAnimal.RECHAZADA
        entrega.observaciones_admin = obs
        entrega.validada_por = request.user
        entrega.fecha_validacion = timezone.now()
        entrega.save()
        return Response(self.get_serializer(entrega).data)


class VistaViewSet(viewsets.GenericViewSet):
    """
    POST /api/vistas/                  -> {animal_id}: se abrió la ficha de un animal
    POST /api/vistas/<id>/cerrar/      -> se cerró la ficha (calcula la duración en el servidor)
    GET  /api/vistas/                  -> (admin) registros; filtros ?animal= ?usuario=
    GET  /api/vistas/resumen/          -> (admin) total y tiempo por usuario y animal
    Solo se registran usuarios autenticados que aceptaron la política de datos.
    """

    serializer_class = VistaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VistaAnimal.objects.select_related("usuario", "animal")

    def _filtrar(self, request):
        qs = self.get_queryset()
        if request.query_params.get("animal"):
            qs = qs.filter(animal=request.query_params["animal"])
        if request.query_params.get("usuario"):
            qs = qs.filter(usuario__username=request.query_params["usuario"])
        return qs

    def create(self, request):
        animal = get_object_or_404(animales_visibles(request.user), pk=request.data.get("animal_id"))
        if request.user.es_admin or not request.user.acepta_politica:
            return Response(status=status.HTTP_204_NO_CONTENT)  # no se registra
        vista = VistaAnimal.objects.create(usuario=request.user, animal=animal)
        return Response({"id": str(vista.pk)}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cerrar")
    def cerrar(self, request, pk=None):
        vista = get_object_or_404(VistaAnimal, pk=pk, usuario=request.user)
        if vista.fin is None:
            vista.fin = timezone.now()
            vista.duracion_segundos = min(
                int((vista.fin - vista.inicio).total_seconds()), MAX_SEGUNDOS_VISTA
            )
            vista.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        if not request.user.es_admin:
            return Response({"detail": "Solo los administradores pueden consultar las vistas."}, status=403)
        return Response(self.get_serializer(self._filtrar(request), many=True).data)

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        if not request.user.es_admin:
            return Response({"detail": "Solo los administradores pueden consultar las vistas."}, status=403)
        acumulado = {}
        for v in self._filtrar(request):
            clave = (v.usuario_id, v.animal_id)
            fila = acumulado.setdefault(clave, {
                "usuario_username": v.usuario.username, "animal_id": str(v.animal_id),
                "animal_nombre": v.animal.nombre or "Sin nombre", "veces": 0,
                "segundos_totales": 0, "ultima_vista": v.inicio,
            })
            fila["veces"] += 1
            fila["segundos_totales"] += v.duracion_segundos
            fila["ultima_vista"] = max(fila["ultima_vista"], v.inicio)
        filas = sorted(acumulado.values(), key=lambda f: f["segundos_totales"], reverse=True)
        return Response(filas)
