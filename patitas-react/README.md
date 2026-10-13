# Patitas Amigables — Frontend (React + Vite)

Interfaz en React que consume la API de Django (`patitas-backend`).

## Instalar y correr

```bash
cd patitas-react
npm install

cp .env.example .env    # ajusta VITE_API_URL si tu backend no está en el 8000

npm run dev
```

Abre <http://localhost:5173>.

> **El backend debe estar corriendo primero**, si no la página de inicio mostrará
> un aviso de que no pudo conectarse.

## Variables de entorno

| Variable | Valor por defecto |
|---|---|
| `VITE_API_URL` | `http://127.0.0.1:8000/api` |

## Estructura

```
src/
  api/client.js          Cliente HTTP: tokens JWT y refresh automático
  context/
    AuthContext.jsx      Sesión: login, registro, perfil, contraseña
    AnimalsContext.jsx   Listado y registro de animales
  components/
    Layout.jsx           Menú lateral + hamburguesa móvil
    PetsMap.jsx          Mapa con las mascotas y botón "Localizarme"
    LocationPickerMap.jsx  Mapa para elegir dónde se encontró al animal
    RequireAuth.jsx      Protege las rutas privadas
  pages/                 Home, Login, Register, Profile, ProfileEdit,
                         AddAnimal, About, Contact
  styles/                CSS del proyecto original (mismos colores y diseño)
```

## Rutas

| Ruta | Página | Requiere sesión |
|---|---|---|
| `/` | Inicio: mapa + mascotas | No |
| `/login` | Iniciar sesión | No |
| `/registro` | Crear cuenta | No |
| `/nosotros` | Quiénes somos | No |
| `/contacto` | Contacto | No |
| `/perfil` | Ver perfil | Sí |
| `/perfil/editar` | Editar perfil y contraseña | Sí |
| `/registrar-animal` | Registrar mascota | Sí |

## Cómo se conecta con Django

- El login guarda `access` y `refresh` en `localStorage`.
- Cada petición privada manda la cabecera `Authorization: Bearer <access>`.
- Si el backend responde 401, el cliente pide un token nuevo con el `refresh` y
  reintenta la petición una sola vez. Si tampoco sirve, cierra la sesión.
- El registro de animales se envía como `FormData` porque incluye la foto.
- Las imágenes se leen del campo `foto_url` que devuelve el backend.

## Compilar para producción

```bash
npm run build     # genera dist/
npm run preview
```
