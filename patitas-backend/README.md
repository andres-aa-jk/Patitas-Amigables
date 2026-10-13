# Patitas Amigables — Backend (Django + DRF + MongoDB)

API REST que alimenta el frontend de React.

---

## 1. Crear la base de datos en MongoDB

**Lo primero que hay que entender: en MongoDB no se "crea" la base de datos a mano.**
No existe un `CREATE DATABASE` como en MySQL o PostgreSQL. La base de datos y sus
colecciones (el equivalente a las tablas) se crean **solas** la primera vez que se
insertan datos. Lo único que necesitas es el servidor y la cadena de conexión.

### Opción A — MongoDB Atlas (en la nube, gratis) ← recomendado

1. Entra a <https://www.mongodb.com/cloud/atlas> y crea una cuenta.
2. **Build a Database** → elige el plan **M0 (Free)** → elige la región más cercana
   (por ejemplo `us-east-1`) → **Create Deployment**.
3. **Database Access** (menú izquierdo) → **Add New Database User**:
   - Authentication Method: *Password*
   - Usuario: `patitas_user`
   - Contraseña: genera una y **guárdala**
   - Rol: *Read and write to any database*
4. **Network Access** → **Add IP Address**:
   - Para desarrollo: *Allow access from anywhere* (`0.0.0.0/0`)
   - En producción: pon solo la IP de tu servidor.
5. **Database** → botón **Connect** → **Drivers** → **Python** → copia la URI:

```
mongodb+srv://patitas_user:<db_password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

> Reemplaza `<db_password>` por la contraseña real. Si tiene caracteres especiales
> (`@`, `:`, `/`, `#`) debes codificarlos en URL: `@` → `%40`, `#` → `%23`, etc.

### Opción B — MongoDB local

1. Instala **MongoDB Community Server** desde
   <https://www.mongodb.com/try/download/community>.
2. Arranca el servicio:
   - Windows: se instala como servicio y arranca solo.
   - macOS (Homebrew): `brew services start mongodb-community`
   - Linux: `sudo systemctl start mongod`
3. Tu URI es simplemente: `mongodb://localhost:27017`

### Verificar que la base de datos se creó

Con **MongoDB Compass** (interfaz gráfica) o con `mongosh`:

```bash
mongosh "TU_URI_AQUI"

show dbs                  # aparece patitas_amigables después del migrate
use patitas_amigables
show collections          # users_user, pets_animal, django_migrations, ...
db.pets_animal.find()     # ver los animales registrados
```

---

## 2. Instalar y correr el backend

```bash
cd patitas-backend

# Entorno virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Configuración
cp .env.example .env
# Edita .env y pon tu MONGODB_URI

# Crear las colecciones en MongoDB
python manage.py makemigrations
python manage.py migrate

# Usuario administrador
python manage.py createsuperuser

python manage.py runserver
```

La API queda en <http://127.0.0.1:8000/api/> y el admin en
<http://127.0.0.1:8000/admin/>.

> **Importante:** las migraciones **no** vienen incluidas en el repositorio a
> propósito. Debes generarlas tú con `makemigrations` teniendo ya configurada la
> URI de Mongo, porque los tipos de campo dependen del backend de base de datos.

---

## 3. Endpoints

### Autenticación

| Método | Ruta | Body | Respuesta |
|---|---|---|---|
| POST | `/api/auth/register/` | `username, email, direccion, numero, password1, password2` | `access, refresh, user` |
| POST | `/api/auth/login/` | `username, password` | `access, refresh, user` |
| POST | `/api/auth/refresh/` | `refresh` | `access` |
| GET | `/api/auth/me/` | — | datos del usuario |
| PATCH | `/api/auth/me/` | `username, email, direccion, numero` | usuario actualizado |
| POST | `/api/auth/change-password/` | `old_password, new_password1, new_password2` | `detail` |

### Animales

| Método | Ruta | Notas |
|---|---|---|
| GET | `/api/animales/` | Público. Filtros: `?especie=perro&estado_salud=enfermo` |
| POST | `/api/animales/` | Requiere token. Enviar como **multipart/form-data** por la foto |
| GET | `/api/animales/<id>/` | Detalle |
| PATCH / DELETE | `/api/animales/<id>/` | Solo el dueño del registro |
| GET | `/api/animales/cercanos/?lat=&lng=&radio=1000` | Radio en metros |
| GET | `/api/animales/mis-animales/` | Los del usuario autenticado |

### Autenticación en las peticiones

```
Authorization: Bearer <access_token>
```

El access token dura 8 horas; el refresh, 7 días. El cliente de React renueva el
access automáticamente cuando recibe un 401.

---

## 4. Notas sobre MongoDB

- **Los IDs son `ObjectId`**, no números enteros. En el JSON viajan como texto,
  por ejemplo `"507f1f77bcf86cd799439011"`. Por eso el React nunca debe asumir
  que el id es numérico.
- **`latitud` y `longitud` son `FloatField`** (en el proyecto original en Django
  con SQL eran `DecimalField`). En Mongo los flotantes son el tipo natural y
  además permiten crear índices geoespaciales `2dsphere` más adelante si quieres
  reemplazar el cálculo Haversine por una consulta `$near` nativa.
- Se usa **`django-mongodb-backend`**, que es el backend **oficial de MongoDB**
  (disponible de forma general desde septiembre de 2025). No uses *Djongo*: está
  abandonado y falla con las versiones actuales de Django.
- La versión del paquete debe coincidir con la de Django: para Django 5.2 se usa
  `django-mongodb-backend==5.2.*`.
- Las fotos **no** se guardan en Mongo: se guardan en la carpeta `media/` y en la
  base de datos solo queda la ruta. En producción conviene usar S3 o Cloudinary.

---

## 5. Problemas frecuentes

| Error | Causa y solución |
|---|---|
| `ServerSelectionTimeoutError` | Mongo no está corriendo, o tu IP no está en *Network Access* de Atlas. |
| `Authentication failed` | Usuario o contraseña mal en la URI. Recuerda codificar los caracteres especiales. |
| `CORS policy: No 'Access-Control-Allow-Origin'` | Agrega la URL del frontend a `CORS_ALLOWED_ORIGINS` en el `.env`. |
| `no such column` / campos raros | Borra las migraciones y vuelve a correr `makemigrations` con la URI de Mongo ya configurada. |
| El 401 no se recupera solo | Revisa que `VITE_API_URL` del frontend apunte al puerto correcto. |
