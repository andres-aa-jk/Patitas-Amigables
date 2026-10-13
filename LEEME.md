# Patitas Amigables — Guía de puesta en marcha

Proyecto dividido en dos partes:

```
patitas-backend/   API REST con Django + Django REST Framework + MongoDB
patitas-react/     Interfaz en React + Vite
```

Hay que levantar **primero el backend** y después el frontend.

---

## Paso 1 — Base de datos en MongoDB

En MongoDB **no se crea la base de datos a mano**. No hay un `CREATE DATABASE`
como en MySQL. La base y sus colecciones nacen solas la primera vez que se
guardan datos, cuando corras `python manage.py migrate`.

Lo único que necesitas conseguir es la **cadena de conexión (URI)**.

### Con MongoDB Atlas (nube, gratis)

1. Crea una cuenta en <https://www.mongodb.com/cloud/atlas>.
2. **Build a Database** → plan **M0 (Free)** → **Create Deployment**.
3. **Database Access** → **Add New Database User**:
   usuario, contraseña, y rol *Read and write to any database*.
4. **Network Access** → **Add IP Address** → para desarrollo, *Allow access from
   anywhere* (`0.0.0.0/0`).
5. **Database** → **Connect** → **Drivers** → **Python** → copia la URI:

```
mongodb+srv://usuario:contraseña@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

Si la contraseña tiene caracteres especiales, codifícalos: `@` → `%40`,
`#` → `%23`, `/` → `%2F`.

### Con MongoDB local

Instala MongoDB Community Server y arranca el servicio. Tu URI es:

```
mongodb://localhost:27017
```

---

## Paso 2 — Backend

```bash
cd patitas-backend

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
```

Edita el `.env` y pon tu URI:

```
SECRET_KEY=una-clave-larga-y-secreta
DEBUG=True
MONGODB_URI=mongodb+srv://usuario:contraseña@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_NAME=patitas_amigables
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Luego:

```bash
python manage.py makemigrations     # genera las migraciones
python manage.py migrate            # <-- aquí Mongo crea la BD y las colecciones
python manage.py createsuperuser
python manage.py runserver
```

Backend en <http://127.0.0.1:8000> · Admin en <http://127.0.0.1:8000/admin/>

> Las migraciones no vienen incluidas a propósito: debes generarlas tú con la URI
> de Mongo ya configurada, porque los tipos de campo dependen del motor de base
> de datos.

### Comprobar que la base se creó

```bash
mongosh "TU_URI"
show dbs
use patitas_amigables
show collections        # users_user, pets_animal, django_migrations, ...
```

---

## Paso 3 — Frontend

En **otra terminal**, sin cerrar la del backend:

```bash
cd patitas-react
npm install
cp .env.example .env
npm run dev
```

Frontend en <http://localhost:5173>

---

## Cómo se conectan las dos partes

1. El React manda usuario y contraseña a `/api/auth/login/`.
2. Django responde con dos tokens JWT: `access` (8 horas) y `refresh` (7 días).
3. El React los guarda y manda `Authorization: Bearer <access>` en cada petición
   privada.
4. Cuando el `access` vence, Django responde 401; el cliente pide uno nuevo con
   el `refresh` y reintenta solo. Si el refresh también venció, cierra sesión.
5. Las fotos se suben como `multipart/form-data`, se guardan en `media/` y el
   backend devuelve la ruta completa en el campo `foto_url`.

`CORS_ALLOWED_ORIGINS` es lo que permite que el navegador acepte las respuestas
de Django viniendo desde otro puerto. Si cambias el puerto del frontend, tienes
que actualizarlo.

---

## Endpoints

### Autenticación
- `POST /api/auth/register/` — `username, email, direccion, numero, password1, password2`
- `POST /api/auth/login/` — `username, password`
- `POST /api/auth/refresh/` — `refresh`
- `GET | PATCH /api/auth/me/`
- `POST /api/auth/change-password/`

### Animales
- `GET /api/animales/` — público, admite `?especie=` y `?estado_salud=`
- `POST /api/animales/` — requiere token, multipart
- `GET | PATCH | DELETE /api/animales/<id>/` — editar y borrar solo el dueño
- `GET /api/animales/cercanos/?lat=&lng=&radio=1000` — radio en metros
- `GET /api/animales/mis-animales/`

---

## Diferencias con el proyecto original en Django

| Antes | Ahora | Por qué |
|---|---|---|
| Plantillas HTML de Django | React consumiendo una API | Separación de frontend y backend |
| Sesiones con cookies | Tokens JWT | Es lo normal cuando el frontend va aparte |
| SQLite / SQL | MongoDB | Requisito del proyecto |
| `latitud`/`longitud` como `DecimalField` | `FloatField` | Es el tipo natural en Mongo y permite índices geoespaciales |
| IDs numéricos | `ObjectId` (texto) | Así funciona MongoDB |

El diseño visual (colores, tipografía, menú lateral, tarjetas, mapas) se mantuvo
igual al original.

---

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `ServerSelectionTimeoutError` | Mongo apagado, o tu IP no está autorizada en *Network Access* de Atlas. |
| `Authentication failed` | Usuario o contraseña mal en la URI; revisa los caracteres especiales. |
| Error de CORS en la consola | Agrega la URL del frontend a `CORS_ALLOWED_ORIGINS`. |
| La página dice que no conecta | El backend no está corriendo, o `VITE_API_URL` apunta al puerto equivocado. |
| Las fotos no se ven | Revisa que `DEBUG=True` en desarrollo; es lo que hace que Django sirva `media/`. |
| Campos raros tras cambiar de motor | Borra las migraciones y vuelve a correr `makemigrations`. |

---

## Roles, moderación, adopción y entrega

### Qué cambia
- **Roles:** `usuario` y `admin`. El rol solo se asigna desde `/admin/` (o con `createsuperuser`); nunca desde la API.
- **Moderación:** los animales que registra un usuario quedan *pendientes*; solo se ven en el mapa cuando un admin los aprueba. El admin ve posibles duplicados (huella de imagen dHash) como sugerencia, nunca como rechazo automático.
- **Adopción:** botón **Adoptar** en el mapa → formulario → el admin aprueba o rechaza. Al aprobar, el animal pasa a *en entrega* y sale del mapa.
- **Entrega:** el adoptante sube una foto de recogida (con autorización de imagen); el refugio puede confirmar y el admin valida. Al validar, el animal queda *adoptado*. Las fotos se guardan en `media_privado/` y solo las ven el adoptante, el refugio dueño y los admins.
- **Fichas consultadas:** se registra (solo usuarios con sesión que aceptaron la política) qué animal abrieron y por cuánto tiempo (tope 30 min por vista). Solo lo ve el admin.
- Se corrigió el mapa de *Registrar animal* (altura 0 px) y su centro por defecto (ahora Mosquera), y el error de JavaScript de Leaflet al cambiar de página.

### Pasos tras actualizar el código
```bash
cd patitas-backend
python manage.py makemigrations users pets
python manage.py migrate
python manage.py aprobar_existentes     # una sola vez: publica los animales que ya estaban registrados
python manage.py createsuperuser        # el superusuario es admin automáticamente
```
Para dar rol admin a otra cuenta: `/admin/` → Usuarios → campo *Rol*.

### Retención de datos
```bash
python manage.py purgar_vistas --dias 90   # programar periódicamente
```

### Endpoints nuevos
| Método y ruta | Acceso |
|---|---|
| `GET /api/animales/pendientes/` , `POST /api/animales/<id>/revisar/` | admin |
| `POST /api/solicitudes/` , `GET /api/solicitudes/` | autenticado (el admin ve todas) |
| `POST /api/solicitudes/<id>/revisar/` | admin |
| `POST /api/entregas/` , `GET /api/entregas/` , `GET /api/entregas/<id>/foto/` | adoptante, refugio dueño o admin |
| `POST /api/entregas/<id>/confirmar/` | refugio dueño |
| `POST /api/entregas/<id>/validar/` | admin |
| `POST /api/vistas/` , `POST /api/vistas/<id>/cerrar/` | autenticado |
| `GET /api/vistas/` , `GET /api/vistas/resumen/` | admin |

### Pruebas
```bash
python manage.py test pruebas -v 2      # 66 pruebas (API original + roles, moderación, adopción, entrega, vistas, duplicados)
```
Antes de producción: servir `media_privado/` solo mediante la API (ya ocurre), usar HTTPS y publicar la política de tratamiento de datos que menciona el registro.
