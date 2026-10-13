const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

const ACCESS_KEY = 'patitas_access';
const REFRESH_KEY = 'patitas_refresh';

export const tokens = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  save({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

/** Convierte los errores de DRF en un texto legible. */
function parseError(data) {
  if (!data) return 'Ocurrió un error inesperado.';
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const first = Object.values(data)[0];
  if (Array.isArray(first)) return first[0];
  return String(first);
}

async function refreshAccessToken() {
  const refresh = tokens.refresh;
  if (!refresh) return false;

  const res = await fetch(`${BASE_URL}/auth/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) {
    tokens.clear();
    return false;
  }
  const data = await res.json();
  tokens.save({ access: data.access });
  return true;
}

/**
 * Hace una petición a la API.
 * Si el body es FormData no se pone Content-Type (lo define el navegador).
 * Si el access token expiró, intenta refrescarlo una vez y reintenta.
 */
export async function apiFetch(path, { method = 'GET', body, auth = true, retry = true } = {}) {
  const headers = {};
  const isFormData = body instanceof FormData;

  if (body && !isFormData) headers['Content-Type'] = 'application/json';
  if (auth && tokens.access) headers['Authorization'] = `Bearer ${tokens.access}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth && retry) {
    const ok = await refreshAccessToken();
    if (ok) {
      return apiFetch(path, { method, body, auth, retry: false });
    }
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const error = new Error(parseError(data));
    error.data = data;
    error.status = res.status;
    throw error;
  }

  return data;
}

/** Descarga un archivo protegido (p. ej. la foto de una entrega) y devuelve una URL local. */
export async function apiBlobUrl(path) {
  const send = () =>
    fetch(`${BASE_URL}${path}`, { headers: { Authorization: `Bearer ${tokens.access}` } });
  let res = await send();
  if (res.status === 401 && (await refreshAccessToken())) res = await send();
  if (!res.ok) throw new Error('No se pudo cargar la imagen.');
  return URL.createObjectURL(await res.blob());
}

export const api = {
  // --- Autenticación ---
  login: (username, password) =>
    apiFetch('/auth/login/', { method: 'POST', body: { username, password }, auth: false }),
  register: (payload) =>
    apiFetch('/auth/register/', { method: 'POST', body: payload, auth: false }),
  me: () => apiFetch('/auth/me/'),
  updateMe: (payload) => apiFetch('/auth/me/', { method: 'PATCH', body: payload }),
  changePassword: (payload) =>
    apiFetch('/auth/change-password/', { method: 'POST', body: payload }),

  // --- Animales ---
  listAnimales: () => apiFetch('/animales/', { auth: false }),
  getAnimal: (id) => apiFetch(`/animales/${id}/`, { auth: false }),
  createAnimal: (formData) =>
    apiFetch('/animales/', { method: 'POST', body: formData }),
  deleteAnimal: (id) => apiFetch(`/animales/${id}/`, { method: 'DELETE' }),
  cercanos: (lat, lng, radio = 1000) =>
    apiFetch(`/animales/cercanos/?lat=${lat}&lng=${lng}&radio=${radio}`, { auth: false }),
  misAnimales: () => apiFetch('/animales/mis-animales/'),

  // --- Moderación de animales (administrador) ---
  animalesPendientes: (estado = 'pendiente') => apiFetch(`/animales/pendientes/?estado=${estado}`),
  revisarAnimal: (id, decision, motivo = '') =>
    apiFetch(`/animales/${id}/revisar/`, { method: 'POST', body: { decision, motivo } }),

  // --- Solicitudes de adopción ---
  crearSolicitud: (payload) => apiFetch('/solicitudes/', { method: 'POST', body: payload }),
  misSolicitudes: (estado = '') =>
    apiFetch(`/solicitudes/${estado ? `?estado=${estado}` : ''}`),
  revisarSolicitud: (id, decision, observaciones = '') =>
    apiFetch(`/solicitudes/${id}/revisar/`, { method: 'POST', body: { decision, observaciones } }),

  // --- Entrega (constancia con foto) ---
  subirEntrega: (formData) => apiFetch('/entregas/', { method: 'POST', body: formData }),
  entregas: (estado = '') => apiFetch(`/entregas/${estado ? `?estado=${estado}` : ''}`),
  confirmarEntrega: (id) => apiFetch(`/entregas/${id}/confirmar/`, { method: 'POST' }),
  validarEntrega: (id, decision, observaciones = '') =>
    apiFetch(`/entregas/${id}/validar/`, { method: 'POST', body: { decision, observaciones } }),

  // --- Vistas de fichas (solo se registran usuarios autenticados) ---
  abrirVista: (animalId) =>
    apiFetch('/vistas/', { method: 'POST', body: { animal_id: animalId } }),
  cerrarVista: (id) => apiFetch(`/vistas/${id}/cerrar/`, { method: 'POST' }),
  resumenVistas: (params = '') => apiFetch(`/vistas/resumen/${params}`),
  vistas: (params = '') => apiFetch(`/vistas/${params}`),
};
