"""Pruebas funcionales de la API de Patitas Amigables (RF-01 a RF-04)."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()
REG = {"username": "ana", "email": "ana@correo.com", "direccion": "Cra 1 #2-3 Mosquera",
       "numero": "3001234567", "password1": "ClaveSegura#2026", "password2": "ClaveSegura#2026",
       "acepta_politica": True}
ANIMAL = {"nombre": "Firulais", "especie": "perro", "raza": "Criollo", "edad": 3,
          "estado_salud": "saludable", "descripcion": "Amistoso", "latitud": 4.7059, "longitud": -74.2309}


def crear_usuario(nombre="u1", rol="usuario"):
    return User.objects.create_user(username=nombre, email=f"{nombre}@c.com",
                                    password="ClaveSegura#2026", rol=rol, acepta_politica=True)


def lista(resp):
    return resp.data["results"] if isinstance(resp.data, dict) else resp.data


class Autenticacion(APITestCase):
    def test_CP01_registro_exitoso_devuelve_tokens(self):
        r = self.client.post("/api/auth/register/", REG, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("access", r.data); self.assertIn("refresh", r.data)
        self.assertEqual(r.data["user"]["username"], "ana")

    def test_CP02_registro_usuario_duplicado(self):
        self.client.post("/api/auth/register/", REG, format="json")
        r = self.client.post("/api/auth/register/", {**REG, "email": "otro@c.com"}, format="json")
        self.assertEqual(r.status_code, 400); self.assertIn("username", r.data)

    def test_CP03_registro_correo_duplicado(self):
        self.client.post("/api/auth/register/", REG, format="json")
        r = self.client.post("/api/auth/register/", {**REG, "username": "otra"}, format="json")
        self.assertEqual(r.status_code, 400); self.assertIn("email", r.data)

    def test_CP04_registro_contrasenas_no_coinciden(self):
        r = self.client.post("/api/auth/register/", {**REG, "password2": "distinta"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_CP05_registro_contrasena_debil(self):
        r = self.client.post("/api/auth/register/", {**REG, "password1": "123", "password2": "123"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_CP06_registro_campos_obligatorios(self):
        r = self.client.post("/api/auth/register/", {"username": "x"}, format="json")
        self.assertEqual(r.status_code, 400)
        for campo in ("email", "direccion", "numero"):
            self.assertIn(campo, r.data)

    def test_CP07_login_correcto(self):
        crear_usuario()
        r = self.client.post("/api/auth/login/", {"username": "u1", "password": "ClaveSegura#2026"}, format="json")
        self.assertEqual(r.status_code, 200); self.assertIn("access", r.data); self.assertEqual(r.data["user"]["username"], "u1")

    def test_CP08_login_credenciales_invalidas(self):
        crear_usuario()
        r = self.client.post("/api/auth/login/", {"username": "u1", "password": "mala"}, format="json")
        self.assertEqual(r.status_code, 401)

    def test_CP09_perfil_requiere_autenticacion(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_CP10_ver_y_editar_perfil(self):
        u = crear_usuario(); self.client.force_authenticate(u)
        self.assertEqual(self.client.get("/api/auth/me/").data["username"], "u1")
        r = self.client.patch("/api/auth/me/", {"direccion": "Nueva dir", "numero": "3110000000"}, format="json")
        self.assertEqual(r.status_code, 200); self.assertEqual(r.data["direccion"], "Nueva dir")

    def test_CP11_cambio_de_contrasena(self):
        u = crear_usuario(); self.client.force_authenticate(u)
        ok = self.client.post("/api/auth/change-password/", {"old_password": "ClaveSegura#2026",
             "new_password1": "NuevaClave#2027", "new_password2": "NuevaClave#2027"}, format="json")
        self.assertEqual(ok.status_code, 200)
        mal = self.client.post("/api/auth/change-password/", {"old_password": "incorrecta",
             "new_password1": "NuevaClave#2028", "new_password2": "NuevaClave#2028"}, format="json")
        self.assertEqual(mal.status_code, 400)

    def test_CP12_refresh_token(self):
        crear_usuario()
        t = self.client.post("/api/auth/login/", {"username": "u1", "password": "ClaveSegura#2026"}, format="json").data
        r = self.client.post("/api/auth/refresh/", {"refresh": t["refresh"]}, format="json")
        self.assertEqual(r.status_code, 200); self.assertIn("access", r.data)


class Animales(APITestCase):
    def setUp(self):
        self.u1 = crear_usuario("u1", "admin"); self.u2 = crear_usuario("u2")

    def test_CP13_crear_animal_autenticado(self):
        self.client.force_authenticate(self.u1)
        r = self.client.post("/api/animales/", ANIMAL, format="json")
        self.assertEqual(r.status_code, 201); self.assertEqual(r.data["registrado_por_username"], "u1")

    def test_CP14_crear_animal_sin_sesion(self):
        self.assertEqual(self.client.post("/api/animales/", ANIMAL, format="json").status_code, 401)

    def test_CP15_listado_publico(self):
        self.client.force_authenticate(self.u1); self.client.post("/api/animales/", ANIMAL, format="json")
        self.client.force_authenticate(None)
        r = self.client.get("/api/animales/")
        self.assertEqual(r.status_code, 200)
        datos = r.data["results"] if isinstance(r.data, dict) else r.data
        self.assertEqual(len(datos), 1)

    def test_CP16_filtros_especie_y_salud(self):
        self.client.force_authenticate(self.u1)
        self.client.post("/api/animales/", ANIMAL, format="json")
        self.client.post("/api/animales/", {**ANIMAL, "especie": "gato", "estado_salud": "lesionado"}, format="json")
        def n(q):
            d = self.client.get("/api/animales/" + q).data
            return len(d["results"] if isinstance(d, dict) else d)
        self.assertEqual(n(""), 2); self.assertEqual(n("?especie=gato"), 1)
        self.assertEqual(n("?estado_salud=lesionado"), 1); self.assertEqual(n("?especie=ave"), 0)

    def test_CP17_validaciones_animal(self):
        self.client.force_authenticate(self.u1)
        self.assertEqual(self.client.post("/api/animales/", {**ANIMAL, "edad": -1}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/animales/", {**ANIMAL, "especie": "dragon"}, format="json").status_code, 400)
        sin_coord = {k: v for k, v in ANIMAL.items() if k not in ("latitud", "longitud")}
        self.assertEqual(self.client.post("/api/animales/", sin_coord, format="json").status_code, 400)

    def test_CP18_cercanos_dentro_y_fuera_del_radio(self):
        self.client.force_authenticate(self.u1)
        self.client.post("/api/animales/", ANIMAL, format="json")  # 4.7059,-74.2309
        self.client.post("/api/animales/", {**ANIMAL, "nombre": "Lejos", "latitud": 4.80, "longitud": -74.10}, format="json")  # ~17 km
        r = self.client.get("/api/animales/cercanos/?lat=4.7060&lng=-74.2310&radio=1000")
        self.assertEqual(r.status_code, 200); self.assertEqual([a["nombre"] for a in r.data], ["Firulais"])
        r = self.client.get("/api/animales/cercanos/?lat=4.7060&lng=-74.2310&radio=30000")
        self.assertEqual(len(r.data), 2)

    def test_CP19_cercanos_sin_parametros(self):
        self.assertEqual(self.client.get("/api/animales/cercanos/").status_code, 400)

    def test_CP20_solo_el_dueno_edita_o_borra(self):
        self.client.force_authenticate(self.u1)
        aid = self.client.post("/api/animales/", ANIMAL, format="json").data["id"]
        self.client.force_authenticate(self.u2)
        self.assertEqual(self.client.patch(f"/api/animales/{aid}/", {"nombre": "X"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/animales/{aid}/").status_code, 403)
        self.client.force_authenticate(self.u1)
        self.assertEqual(self.client.patch(f"/api/animales/{aid}/", {"nombre": "Nuevo"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/animales/{aid}/").status_code, 204)

    def test_CP21_mis_animales(self):
        self.client.force_authenticate(self.u1); self.client.post("/api/animales/", ANIMAL, format="json")
        self.client.force_authenticate(self.u2); self.client.post("/api/animales/", ANIMAL, format="json")
        r = self.client.get("/api/animales/mis-animales/")
        self.assertEqual(len(r.data), 1); self.assertEqual(r.data[0]["registrado_por_username"], "u2")
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/animales/mis-animales/").status_code, 401)
