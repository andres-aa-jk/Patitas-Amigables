"""Pruebas de las funciones nuevas: roles, moderación, adopción, entrega, vistas y duplicados."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageDraw
from rest_framework.test import APITestCase

from pets.imagenes import calcular_hash, distancia
from pets.models import Animal, EntregaAnimal, VistaAnimal

from .test_api import ANIMAL, REG, crear_usuario, lista

SOLICITUD = {"motivo": "Tengo patio amplio y tiempo para cuidarlo.", "tipo_vivienda": "Casa con patio",
             "tiene_otras_mascotas": False, "experiencia": "Tuve perros", "acepta_visita": True}


def imagen(semilla=0, nombre="f.png"):
    """Imagen sintética: la semilla cambia la figura, por lo que la huella cambia."""
    img = Image.new("RGB", (120, 120), "white"); d = ImageDraw.Draw(img)
    if semilla == 0:
        d.rectangle([10, 10, 70, 110], fill="black"); d.ellipse([60, 60, 115, 115], fill="gray")
    elif semilla == 1:
        d.polygon([(5, 115), (60, 5), (115, 115)], fill="black"); d.rectangle([0, 0, 40, 30], fill="gray")
    else:
        for i in range(0, 120, 12):
            d.line([(0, i), (120, 120 - i)], fill="black", width=4)
    b = io.BytesIO(); img.save(b, "PNG")
    return SimpleUploadedFile(nombre, b.getvalue(), content_type="image/png")


class Base(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "admin")
        self.refugio = crear_usuario("refugio")
        self.adoptante = crear_usuario("adoptante")
        self.otro = crear_usuario("otro")

    def as_(self, u):
        self.client.force_authenticate(u)

    def animal_aprobado(self, **extra):
        self.as_(self.refugio)
        r = self.client.post("/api/animales/", {**ANIMAL, **extra}, format="json")
        self.assertEqual(r.status_code, 201)
        aid = r.data["id"]
        self.as_(self.admin)
        self.client.post(f"/api/animales/{aid}/revisar/", {"decision": "aprobar"}, format="json")
        return aid


class Roles(Base):
    def test_RL01_registro_siempre_crea_usuario_normal(self):
        r = self.client.post("/api/auth/register/", {**REG, "rol": "admin"}, format="json")
        self.assertEqual(r.status_code, 201); self.assertEqual(r.data["user"]["rol"], "usuario")

    def test_RL02_no_se_puede_subir_de_rol_editando_el_perfil(self):
        self.as_(self.otro)
        self.client.patch("/api/auth/me/", {"rol": "admin", "is_staff": True}, format="json")
        self.otro.refresh_from_db()
        self.assertEqual(self.otro.rol, "usuario"); self.assertFalse(self.otro.is_staff)

    def test_RL03_login_devuelve_el_rol(self):
        r = self.client.post("/api/auth/login/", {"username": "admin1", "password": "ClaveSegura#2026"}, format="json")
        self.assertEqual(r.data["user"]["rol"], "admin")

    def test_RL04_registro_exige_aceptar_la_politica(self):
        r = self.client.post("/api/auth/register/", {**REG, "acepta_politica": False}, format="json")
        self.assertEqual(r.status_code, 400); self.assertIn("acepta_politica", r.data)

    def test_RL05_endpoints_de_admin_rechazan_a_usuarios(self):
        self.as_(self.otro)
        for url in ("/api/animales/pendientes/", "/api/vistas/", "/api/vistas/resumen/"):
            self.assertEqual(self.client.get(url).status_code, 403, url)


class Moderacion(Base):
    def test_MD01_animal_de_usuario_queda_pendiente_y_no_es_publico(self):
        self.as_(self.refugio)
        r = self.client.post("/api/animales/", ANIMAL, format="json")
        self.assertEqual(r.data["estado_publicacion"], "pendiente")
        self.client.force_authenticate(None)
        self.assertEqual(len(lista(self.client.get("/api/animales/"))), 0)
        self.as_(self.refugio)
        self.assertEqual(len(lista(self.client.get("/api/animales/"))), 1)  # el dueño sí lo ve

    def test_MD02_admin_aprueba_y_se_publica(self):
        aid = self.animal_aprobado()
        self.client.force_authenticate(None)
        self.assertEqual(len(lista(self.client.get("/api/animales/"))), 1)
        self.assertEqual(len(self.client.get("/api/animales/cercanos/?lat=4.7059&lng=-74.2309").data), 1)

    def test_MD03_rechazo_exige_motivo_y_oculta(self):
        self.as_(self.refugio); aid = self.client.post("/api/animales/", ANIMAL, format="json").data["id"]
        self.as_(self.admin)
        self.assertEqual(self.client.post(f"/api/animales/{aid}/revisar/", {"decision": "rechazar"}, format="json").status_code, 400)
        r = self.client.post(f"/api/animales/{aid}/revisar/", {"decision": "rechazar", "motivo": "Foto borrosa"}, format="json")
        self.assertEqual(r.data["estado_publicacion"], "rechazado")
        self.client.force_authenticate(None)
        self.assertEqual(len(lista(self.client.get("/api/animales/"))), 0)

    def test_MD04_usuario_no_puede_revisar_ni_forzar_el_estado(self):
        self.as_(self.refugio)
        r = self.client.post("/api/animales/", {**ANIMAL, "estado_publicacion": "aprobado"}, format="json")
        self.assertEqual(r.data["estado_publicacion"], "pendiente")
        aid = r.data["id"]
        self.assertEqual(self.client.post(f"/api/animales/{aid}/revisar/", {"decision": "aprobar"}, format="json").status_code, 403)

    def test_MD05_editar_devuelve_el_animal_a_revision(self):
        aid = self.animal_aprobado()
        self.as_(self.refugio)
        r = self.client.patch(f"/api/animales/{aid}/", {"descripcion": "Cambio"}, format="json")
        self.assertEqual(r.data["estado_publicacion"], "pendiente")

    def test_MD06_cola_de_pendientes_del_admin(self):
        self.as_(self.refugio); self.client.post("/api/animales/", ANIMAL, format="json")
        self.as_(self.admin)
        self.assertEqual(len(self.client.get("/api/animales/pendientes/").data), 1)


class Duplicados(Base):
    def test_DU01_huella_igual_y_distinta(self):
        self.assertEqual(distancia(calcular_hash(imagen(0)), calcular_hash(imagen(0))), 0)
        self.assertGreater(distancia(calcular_hash(imagen(0)), calcular_hash(imagen(1))), 10)

    def test_DU02_archivo_que_no_es_imagen_se_rechaza(self):
        self.as_(self.refugio)
        falso = SimpleUploadedFile("x.png", b"no soy una imagen", content_type="image/png")
        r = self.client.post("/api/animales/", {**ANIMAL, "foto": falso}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_DU03_admin_ve_el_posible_duplicado(self):
        self.as_(self.refugio)
        self.client.post("/api/animales/", {**ANIMAL, "nombre": "Original", "foto": imagen(0)}, format="multipart")
        self.client.post("/api/animales/", {**ANIMAL, "nombre": "Repetido", "foto": imagen(0, "g.png")}, format="multipart")
        self.client.post("/api/animales/", {**ANIMAL, "nombre": "Distinto", "foto": imagen(1, "h.png")}, format="multipart")
        self.as_(self.admin)
        datos = {a["nombre"]: a for a in self.client.get("/api/animales/pendientes/").data}
        self.assertEqual([d["nombre"] for d in datos["Repetido"]["posibles_duplicados"]], ["Original"])
        self.assertEqual(datos["Distinto"]["posibles_duplicados"], [])


class Adopcion(Base):
    def solicitar(self, aid, usuario=None):
        self.as_(usuario or self.adoptante)
        return self.client.post("/api/solicitudes/", {**SOLICITUD, "animal_id": aid}, format="json")

    def test_AD01_solicitud_valida(self):
        aid = self.animal_aprobado()
        r = self.solicitar(aid)
        self.assertEqual(r.status_code, 201); self.assertEqual(r.data["estado"], "pendiente")

    def test_AD02_requiere_sesion(self):
        aid = self.animal_aprobado()
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post("/api/solicitudes/", {**SOLICITUD, "animal_id": aid}, format="json").status_code, 401)

    def test_AD03_no_se_puede_adoptar_animal_no_aprobado_ni_propio(self):
        self.as_(self.refugio); aid = self.client.post("/api/animales/", ANIMAL, format="json").data["id"]
        self.assertEqual(self.solicitar(aid).status_code, 404)  # pendiente: no existe para el público
        aid2 = self.animal_aprobado()
        self.assertEqual(self.solicitar(aid2, self.refugio).status_code, 400)  # es suyo

    def test_AD04_validaciones_del_formulario(self):
        aid = self.animal_aprobado(); self.as_(self.adoptante)
        corto = self.client.post("/api/solicitudes/", {**SOLICITUD, "animal_id": aid, "motivo": "ok"}, format="json")
        self.assertEqual(corto.status_code, 400); self.assertIn("motivo", corto.data)
        sin_visita = self.client.post("/api/solicitudes/", {**SOLICITUD, "animal_id": aid, "acepta_visita": False}, format="json")
        self.assertEqual(sin_visita.status_code, 400)

    def test_AD05_no_se_duplica_la_solicitud_pendiente(self):
        aid = self.animal_aprobado(); self.solicitar(aid)
        self.assertEqual(self.solicitar(aid).status_code, 400)

    def test_AD06_cada_usuario_ve_solo_las_suyas_y_el_admin_todas(self):
        aid = self.animal_aprobado(); self.solicitar(aid); self.solicitar(aid, self.otro)
        self.as_(self.adoptante); self.assertEqual(len(lista(self.client.get("/api/solicitudes/"))), 1)
        self.as_(self.admin); self.assertEqual(len(lista(self.client.get("/api/solicitudes/"))), 2)

    def test_AD07_aprobar_pone_el_animal_en_entrega_y_cierra_las_demas(self):
        aid = self.animal_aprobado()
        s1 = self.solicitar(aid).data["id"]; s2 = self.solicitar(aid, self.otro).data["id"]
        self.as_(self.admin)
        r = self.client.post(f"/api/solicitudes/{s1}/revisar/", {"decision": "aprobar"}, format="json")
        self.assertEqual(r.data["estado"], "aprobada")
        self.assertEqual(Animal.objects.get(pk=aid).estado_adopcion, "en_entrega")
        self.assertEqual(self.client.get(f"/api/solicitudes/{s2}/").data["estado"], "rechazada")
        self.client.force_authenticate(None)  # ya no aparece en el mapa
        self.assertEqual(len(lista(self.client.get("/api/animales/"))), 0)

    def test_AD08_rechazar_exige_observaciones_y_un_usuario_no_revisa(self):
        aid = self.animal_aprobado(); sid = self.solicitar(aid).data["id"]
        self.assertEqual(self.client.post(f"/api/solicitudes/{sid}/revisar/", {"decision": "aprobar"}, format="json").status_code, 403)
        self.as_(self.admin)
        self.assertEqual(self.client.post(f"/api/solicitudes/{sid}/revisar/", {"decision": "rechazar"}, format="json").status_code, 400)
        r = self.client.post(f"/api/solicitudes/{sid}/revisar/", {"decision": "rechazar", "observaciones": "Sin espacio"}, format="json")
        self.assertEqual(r.data["estado"], "rechazada")
        self.assertEqual(Animal.objects.get(pk=aid).estado_adopcion, "disponible")


class Entrega(Adopcion):
    def en_entrega(self):
        aid = self.animal_aprobado(); sid = self.solicitar(aid).data["id"]
        self.as_(self.admin); self.client.post(f"/api/solicitudes/{sid}/revisar/", {"decision": "aprobar"}, format="json")
        return aid, sid

    def subir(self, sid, usuario=None, **extra):
        self.as_(usuario or self.adoptante)
        datos = {"solicitud": sid, "foto": imagen(2, "e.png"), "consentimiento_imagen": True, **extra}
        return self.client.post("/api/entregas/", datos, format="multipart")

    def test_EN01_flujo_completo_hasta_adoptado(self):
        aid, sid = self.en_entrega()
        r = self.subir(sid); self.assertEqual(r.status_code, 201); eid = r.data["id"]
        self.assertEqual(r.data["estado"], "pendiente"); self.assertNotIn("foto_url", r.data)
        self.as_(self.refugio)
        self.assertTrue(self.client.post(f"/api/entregas/{eid}/confirmar/").data["confirmada_por_refugio"])
        self.as_(self.admin)
        v = self.client.post(f"/api/entregas/{eid}/validar/", {"decision": "validar"}, format="json")
        self.assertEqual(v.data["estado"], "validada")
        self.assertEqual(Animal.objects.get(pk=aid).estado_adopcion, "adoptado")

    def test_EN02_exige_consentimiento_de_imagen(self):
        _, sid = self.en_entrega()
        r = self.subir(sid, consentimiento_imagen=False)
        self.assertEqual(r.status_code, 400); self.assertIn("consentimiento_imagen", r.data)

    def test_EN03_solo_el_solicitante_con_solicitud_aprobada_sube_la_foto(self):
        aid = self.animal_aprobado(); sid = self.solicitar(aid).data["id"]
        self.assertEqual(self.subir(sid).status_code, 400)  # aún pendiente
        self.as_(self.admin); self.client.post(f"/api/solicitudes/{sid}/revisar/", {"decision": "aprobar"}, format="json")
        self.assertEqual(self.subir(sid, self.otro).status_code, 404)  # no es su solicitud

    def test_EN04_una_sola_constancia_activa_y_se_puede_reintentar_si_se_rechaza(self):
        _, sid = self.en_entrega()
        eid = self.subir(sid).data["id"]
        self.assertEqual(self.subir(sid).status_code, 400)
        self.as_(self.admin)
        self.assertEqual(self.client.post(f"/api/entregas/{eid}/validar/", {"decision": "rechazar"}, format="json").status_code, 400)
        self.client.post(f"/api/entregas/{eid}/validar/", {"decision": "rechazar", "observaciones": "No se ve el animal"}, format="json")
        self.assertEqual(self.subir(sid).status_code, 201)

    def test_EN05_la_foto_es_privada(self):
        _, sid = self.en_entrega(); eid = self.subir(sid).data["id"]
        for u, esperado in ((self.adoptante, 200), (self.refugio, 200), (self.admin, 200), (self.otro, 404)):
            self.as_(u); self.assertEqual(self.client.get(f"/api/entregas/{eid}/foto/").status_code, esperado, u.username)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/entregas/{eid}/foto/").status_code, 401)
        self.assertNotIn("/media/", EntregaAnimal.objects.get(pk=eid).foto.path.replace("media_privado", ""))

    def test_EN06_solo_el_refugio_dueno_confirma_y_solo_el_admin_valida(self):
        _, sid = self.en_entrega(); eid = self.subir(sid).data["id"]
        self.as_(self.adoptante)
        self.assertEqual(self.client.post(f"/api/entregas/{eid}/confirmar/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/entregas/{eid}/validar/", {"decision": "validar"}, format="json").status_code, 403)

    def test_EN07_el_admin_ve_si_la_foto_ya_se_uso(self):
        _, sid = self.en_entrega(); self.subir(sid)
        # un animal publicado con la misma foto de la entrega
        self.as_(self.refugio)
        self.client.post("/api/animales/", {**ANIMAL, "nombre": "Misma", "foto": imagen(2, "z.png")}, format="multipart")
        self.as_(self.admin)
        e = lista(self.client.get("/api/entregas/"))[0]
        self.assertTrue(any(h["tipo"] == "animal" for h in e["foto_repetida"]))


class Vistas(Base):
    def test_VS01_registra_apertura_y_cierre_con_duracion(self):
        aid = self.animal_aprobado(); self.as_(self.adoptante)
        vid = self.client.post("/api/vistas/", {"animal_id": aid}, format="json").data["id"]
        self.assertEqual(self.client.post(f"/api/vistas/{vid}/cerrar/").status_code, 204)
        v = VistaAnimal.objects.get(pk=vid)
        self.assertIsNotNone(v.fin); self.assertGreaterEqual(v.duracion_segundos, 0)

    def test_VS02_la_duracion_se_limita(self):
        from datetime import timedelta
        aid = self.animal_aprobado(); self.as_(self.adoptante)
        vid = self.client.post("/api/vistas/", {"animal_id": aid}, format="json").data["id"]
        VistaAnimal.objects.filter(pk=vid).update(inicio=VistaAnimal.objects.get(pk=vid).inicio - timedelta(hours=5))
        self.client.post(f"/api/vistas/{vid}/cerrar/")
        self.assertEqual(VistaAnimal.objects.get(pk=vid).duracion_segundos, 30 * 60)

    def test_VS03_sin_sesion_no_se_registra(self):
        aid = self.animal_aprobado(); self.client.force_authenticate(None)
        self.assertEqual(self.client.post("/api/vistas/", {"animal_id": aid}, format="json").status_code, 401)

    def test_VS04_no_se_registra_si_no_acepto_la_politica(self):
        aid = self.animal_aprobado()
        self.adoptante.acepta_politica = False; self.adoptante.save(); self.as_(self.adoptante)
        self.assertEqual(self.client.post("/api/vistas/", {"animal_id": aid}, format="json").status_code, 204)
        self.assertEqual(VistaAnimal.objects.count(), 0)

    def test_VS05_no_se_puede_cerrar_la_vista_de_otro(self):
        aid = self.animal_aprobado(); self.as_(self.adoptante)
        vid = self.client.post("/api/vistas/", {"animal_id": aid}, format="json").data["id"]
        self.as_(self.otro); self.assertEqual(self.client.post(f"/api/vistas/{vid}/cerrar/").status_code, 404)

    def test_VS06_el_admin_consulta_y_resume_y_el_usuario_no(self):
        aid = self.animal_aprobado()
        for _ in range(2):
            self.as_(self.adoptante)
            vid = self.client.post("/api/vistas/", {"animal_id": aid}, format="json").data["id"]
            self.client.post(f"/api/vistas/{vid}/cerrar/")
        self.as_(self.admin)
        self.assertEqual(len(self.client.get("/api/vistas/").data), 2)
        res = self.client.get("/api/vistas/resumen/").data
        self.assertEqual(res[0]["usuario_username"], "adoptante"); self.assertEqual(res[0]["veces"], 2)
        self.assertEqual(len(self.client.get("/api/vistas/?usuario=otro").data), 0)
        self.as_(self.adoptante); self.assertEqual(self.client.get("/api/vistas/").status_code, 403)

    def test_VS07_las_vistas_del_admin_no_se_registran(self):
        aid = self.animal_aprobado(); self.as_(self.admin)
        self.assertEqual(self.client.post("/api/vistas/", {"animal_id": aid}, format="json").status_code, 204)

    def test_VS08_purga_por_retencion(self):
        from datetime import timedelta
        from django.core.management import call_command
        from django.utils import timezone
        aid = self.animal_aprobado(); self.as_(self.adoptante)
        vid = self.client.post("/api/vistas/", {"animal_id": aid}, format="json").data["id"]
        VistaAnimal.objects.filter(pk=vid).update(inicio=timezone.now() - timedelta(days=120))
        self.client.post("/api/vistas/", {"animal_id": aid}, format="json")
        call_command("purgar_vistas", "--dias", "90", stdout=io.StringIO())
        self.assertEqual(VistaAnimal.objects.count(), 1)
