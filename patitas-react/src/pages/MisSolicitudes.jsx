import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { api } from '../api/client';

const ETIQUETA = {
  pendiente: 'Pendiente', aprobada: 'Aprobada', rechazada: 'Rechazada',
  validada: 'Validada',
};

export default function MisSolicitudes() {
  const { state } = useLocation();
  const [solicitudes, setSolicitudes] = useState([]);
  const [entregas, setEntregas] = useState([]);
  const [error, setError] = useState('');

  const cargar = useCallback(async () => {
    try {
      const [s, e] = await Promise.all([api.misSolicitudes(), api.entregas()]);
      setSolicitudes(Array.isArray(s) ? s : s.results || []);
      setEntregas(Array.isArray(e) ? e : e.results || []);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    cargar();
  }, [cargar]);

  async function confirmar(id) {
    try {
      await api.confirmarEntrega(id);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  // Entregas de animales que registré yo (como refugio) pendientes de mi confirmación.
  const porConfirmar = entregas.filter((e) => !e.confirmada_por_refugio && e.estado === 'pendiente');

  return (
    <div className="panel">
      <h2>Mis solicitudes de adopción</h2>
      {state?.aviso && <div className="alert alert-success">{state.aviso}</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      {solicitudes.length === 0 && <p>Aún no has solicitado ninguna adopción.</p>}
      {solicitudes.map((s) => (
        <div className="item-card" key={s.id}>
          <h3>{s.animal_nombre}</h3>
          <p>Estado: <span className={`badge ${s.estado}`}>{ETIQUETA[s.estado]}</span></p>
          <p>Enviada: {new Date(s.fecha).toLocaleString()}</p>
          {s.observaciones_admin && <p>Observaciones: {s.observaciones_admin}</p>}
          {s.estado === 'aprobada' && !s.entrega_id && (
            <div className="item-actions">
              <Link to={`/entrega/${s.id}`} className="btn">Subir constancia de recogida</Link>
            </div>
          )}
          {s.estado === 'aprobada' && s.entrega_id && <p>Constancia de recogida enviada.</p>}
        </div>
      ))}

      {porConfirmar.length > 0 && (
        <>
          <h2>Entregas de mis animales por confirmar</h2>
          {porConfirmar.map((e) => (
            <div className="item-card" key={e.id}>
              <h3>{e.animal_nombre}</h3>
              <p>El adoptante <strong>{e.adoptante_username}</strong> subió su constancia de recogida.</p>
              <div className="item-actions">
                <button type="button" className="btn" onClick={() => confirmar(e.id)}>
                  Confirmar que lo entregué
                </button>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
