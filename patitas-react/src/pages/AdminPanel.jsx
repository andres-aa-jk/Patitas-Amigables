import { useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';
import FotoProtegida from '../components/FotoProtegida';

const lista = (d) => (Array.isArray(d) ? d : d?.results || []);
const minutos = (s) => (s >= 60 ? `${Math.floor(s / 60)} min ${s % 60} s` : `${s} s`);

function Animales({ avisar }) {
  const [items, setItems] = useState([]);
  const cargar = useCallback(() => api.animalesPendientes().then(setItems).catch((e) => avisar(e.message)), [avisar]);
  useEffect(() => { cargar(); }, [cargar]);

  async function decidir(id, decision) {
    let motivo = '';
    if (decision === 'rechazar') {
      motivo = window.prompt('Motivo del rechazo:') || '';
      if (!motivo.trim()) return;
    }
    try { await api.revisarAnimal(id, decision, motivo); cargar(); } catch (e) { avisar(e.message); }
  }

  if (!items.length) return <p>No hay animales pendientes de revisión.</p>;
  return items.map((a) => (
    <div className="item-card" key={a.id}>
      <h3>{a.nombre || 'Sin nombre'} · {a.especie_display}</h3>
      {a.foto_url && <img className="thumb" src={a.foto_url} alt={a.nombre || 'Animal'} />}
      <p>{a.descripcion}</p>
      <p>Registrado por <strong>{a.registrado_por_username}</strong> · {new Date(a.fecha_registro).toLocaleString()}</p>
      {a.posibles_duplicados.length > 0 && (
        <div className="aviso-dup">
          <strong>Posible duplicado:</strong> la foto se parece a{' '}
          {a.posibles_duplicados.map((d) => `${d.nombre} (diferencia ${d.distancia}/64, ${d.estado_publicacion})`).join('; ')}.
          Es solo una sugerencia: verifica antes de decidir.
        </div>
      )}
      <div className="item-actions">
        <button className="btn" onClick={() => decidir(a.id, 'aprobar')}>Aprobar</button>
        <button className="btn btn-danger" onClick={() => decidir(a.id, 'rechazar')}>Rechazar</button>
      </div>
    </div>
  ));
}

function Solicitudes({ avisar }) {
  const [items, setItems] = useState([]);
  const cargar = useCallback(() => api.misSolicitudes('pendiente').then((d) => setItems(lista(d))).catch((e) => avisar(e.message)), [avisar]);
  useEffect(() => { cargar(); }, [cargar]);

  async function decidir(id, decision) {
    let obs = '';
    if (decision === 'rechazar') {
      obs = window.prompt('Motivo del rechazo:') || '';
      if (!obs.trim()) return;
    }
    try { await api.revisarSolicitud(id, decision, obs); cargar(); } catch (e) { avisar(e.message); }
  }

  if (!items.length) return <p>No hay solicitudes pendientes.</p>;
  return items.map((s) => (
    <div className="item-card" key={s.id}>
      <h3>{s.animal_nombre}</h3>
      <p>Solicitante: <strong>{s.solicitante_username}</strong> · {new Date(s.fecha).toLocaleString()}</p>
      <p><strong>Motivo:</strong> {s.motivo}</p>
      <p><strong>Vivienda:</strong> {s.tipo_vivienda} · Otras mascotas: {s.tiene_otras_mascotas ? 'sí' : 'no'}</p>
      {s.experiencia && <p><strong>Experiencia:</strong> {s.experiencia}</p>}
      <div className="item-actions">
        <button className="btn" onClick={() => decidir(s.id, 'aprobar')}>Aprobar</button>
        <button className="btn btn-danger" onClick={() => decidir(s.id, 'rechazar')}>Rechazar</button>
      </div>
    </div>
  ));
}

function Entregas({ avisar }) {
  const [items, setItems] = useState([]);
  const cargar = useCallback(() => api.entregas('pendiente').then((d) => setItems(lista(d))).catch((e) => avisar(e.message)), [avisar]);
  useEffect(() => { cargar(); }, [cargar]);

  async function decidir(id, decision) {
    let obs = '';
    if (decision === 'rechazar') {
      obs = window.prompt('Motivo del rechazo:') || '';
      if (!obs.trim()) return;
    }
    try { await api.validarEntrega(id, decision, obs); cargar(); } catch (e) { avisar(e.message); }
  }

  if (!items.length) return <p>No hay constancias de entrega pendientes.</p>;
  return items.map((e) => (
    <div className="item-card" key={e.id}>
      <h3>{e.animal_nombre}</h3>
      <p>Adoptante: <strong>{e.adoptante_username}</strong> · {new Date(e.fecha).toLocaleString()}</p>
      <p>Confirmada por el refugio: {e.confirmada_por_refugio ? 'sí' : 'no'}</p>
      {e.latitud != null && <p>Ubicación: {e.latitud.toFixed(5)}, {e.longitud.toFixed(5)}</p>}
      {e.foto_repetida?.length > 0 && (
        <div className="aviso-dup">
          <strong>Foto repetida:</strong> se parece a {e.foto_repetida.map((h) => (h.tipo === 'animal' ? `la foto del animal ${h.nombre}` : 'otra constancia')).join(', ')}.
        </div>
      )}
      <FotoProtegida entregaId={e.id} />
      <div className="item-actions">
        <button className="btn" onClick={() => decidir(e.id, 'validar')}>Validar</button>
        <button className="btn btn-danger" onClick={() => decidir(e.id, 'rechazar')}>Rechazar</button>
      </div>
    </div>
  ));
}

function Vistas({ avisar }) {
  const [filas, setFilas] = useState([]);
  const [usuario, setUsuario] = useState('');
  const cargar = useCallback(() => {
    api.resumenVistas(usuario ? `?usuario=${encodeURIComponent(usuario)}` : '').then(setFilas).catch((e) => avisar(e.message));
  }, [usuario, avisar]);
  useEffect(() => { cargar(); }, [cargar]);

  return (
    <>
      <p className="form-text">
        Solo se registran usuarios con sesión que aceptaron la política de datos. Los registros se
        borran a los 90 días (<code>python manage.py purgar_vistas</code>). El tiempo es una señal
        orientativa: una pestaña abierta no prueba mala intención.
      </p>
      <div className="form-group">
        <input className="form-control" placeholder="Filtrar por usuario" value={usuario}
          onChange={(e) => setUsuario(e.target.value)} />
      </div>
      {!filas.length ? <p>Sin registros.</p> : (
        <div className="tabla-wrap">
          <table className="tabla-simple">
            <thead><tr><th>Usuario</th><th>Animal</th><th>Veces</th><th>Tiempo total</th><th>Última vista</th></tr></thead>
            <tbody>
              {filas.map((f) => (
                <tr key={`${f.usuario_username}-${f.animal_id}`}>
                  <td>{f.usuario_username}</td><td>{f.animal_nombre}</td><td>{f.veces}</td>
                  <td>{minutos(f.segundos_totales)}</td><td>{new Date(f.ultima_vista).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

const PESTANAS = [
  ['animales', 'Animales por aprobar', Animales],
  ['solicitudes', 'Solicitudes de adopción', Solicitudes],
  ['entregas', 'Constancias de entrega', Entregas],
  ['vistas', 'Fichas consultadas', Vistas],
];

export default function AdminPanel() {
  const [tab, setTab] = useState('animales');
  const [error, setError] = useState('');
  const avisar = useCallback((m) => setError(m), []);
  const Activa = PESTANAS.find(([k]) => k === tab)[2];

  return (
    <div className="panel">
      <h2>Panel de administración</h2>
      <div className="panel-tabs">
        {PESTANAS.map(([k, nombre]) => (
          <button key={k} className={tab === k ? 'active' : ''} onClick={() => { setError(''); setTab(k); }}>
            {nombre}
          </button>
        ))}
      </div>
      {error && <div className="alert alert-danger">{error}</div>}
      <Activa avisar={avisar} />
    </div>
  );
}
