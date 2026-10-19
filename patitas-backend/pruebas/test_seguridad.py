"""Pruebas de endurecimiento: tamaño y optimización de fotos, ids inválidos y registro de logins fallidos."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from pets.models import Animal

from .test_api import ANIMAL
from .test_flujo import SOLICITUD, Base, imagen


class Fotos(Base):
    @override_settings(MAX_FOTO_MB=0)
    def test_SG01_foto_demasiado_pesada_se_rechaza(self):
        self.as_(self.refugio)
        r = self.client.post("/api/animales/", {**ANIMAL, "foto": imagen(0)}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("foto", r.data)

    def test_SG02_la_foto_se_guarda_reducida_y_en_jpeg(self):
        grande = io.BytesIO()
        Image.new("RGB", (3000, 2000), "white").save(grande, "PNG")
        foto = SimpleUploadedFile("grande.png", grande.getvalue(), content_type="image/png")
        self.as_(self.refugio)
        r = self.client.post("/api/animales/", {**ANIMAL, "foto": foto}, format="multipart")
        self.assertEqual(r.status_code, 201)
        animal = Animal.objects.get(pk=r.data["id"])
        self.assertTrue(animal.foto.name.endswith(".jpg"))
        with Image.open(animal.foto.path) as img:
            self.assertLessEqual(max(img.size), 1600)


class IdsInvalidos(Base):
    def test_SG03_vista_con_id_invalido_da_404(self):
        self.as_(self.adoptante)
        r = self.client.post("/api/vistas/", {"animal_id": "no-es-un-id"}, format="json")
        self.assertEqual(r.status_code, 404)

    def test_SG04_solicitud_con_id_invalido_da_404(self):
        self.as_(self.adoptante)
        r = self.client.post("/api/solicitudes/", {**SOLICITUD, "animal_id": "no-es-un-id"}, format="json")
        self.assertEqual(r.status_code, 404)

    def test_SG05_cerrar_vista_con_id_invalido_da_404(self):
        self.as_(self.adoptante)
        self.assertEqual(self.client.post("/api/vistas/xyz/cerrar/").status_code, 404)


class RegistroDeActividad(Base):
    def test_SG06_login_fallido_queda_en_el_registro(self):
        with self.assertLogs("patitas.seguridad", level="WARNING") as registro:
            r = self.client.post("/api/auth/login/", {"username": "admin1", "password": "incorrecta"}, format="json")
        self.assertEqual(r.status_code, 401)
        self.assertIn("admin1", registro.output[0])
