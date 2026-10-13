import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const { user } = useAuth();
  const { state } = useLocation();
  const [animales, setAnimales] = useState([]);

  useEffect(() => {
    api.misAnimales().then(setAnimales).catch(() => {});
  }, []);

  return (
    <center>
      <div className="empty-state" style={{ maxWidth: 800 }}>
        <h2>Mi perfil</h2>
        {state?.aviso && <div className="alert alert-success">{state.aviso}</div>}
        <div
          style={{
            background: 'white',
            padding: '1.5rem',
            borderRadius: 12,
            marginTop: '1rem',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
            width: '100%',
          }}
        >
          <p>
            <strong>Usuario:</strong> {user?.username}
          </p>
          <p>
            <strong>Email:</strong> {user?.email}
          </p>
          {user?.direccion && (
            <p>
              <strong>Dirección:</strong> {user.direccion}
            </p>
          )}
          {user?.numero && (
            <p>
              <strong>Teléfono:</strong> {user.numero}
            </p>
          )}
        </div>
        {animales.length > 0 && (
          <div style={{ marginTop: '1.5rem', width: '100%', textAlign: 'left' }}>
            <h3>Mis animales registrados</h3>
            {animales.map((a) => (
              <div className="item-card" key={a.id}>
                <strong>{a.nombre || 'Sin nombre'}</strong>{' '}
                <span className={`badge ${a.estado_publicacion}`}>{a.estado_publicacion}</span>{' '}
                {a.estado_publicacion === 'aprobado' && (
                  <span className={`badge ${a.estado_adopcion}`}>{a.estado_adopcion.replace('_', ' ')}</span>
                )}
                {a.estado_publicacion === 'rechazado' && a.motivo_rechazo && (
                  <p>Motivo del rechazo: {a.motivo_rechazo}</p>
                )}
              </div>
            ))}
          </div>
        )}
        <div style={{ marginTop: '1rem' }}>
          <Link to="/perfil/editar" className="btn">
            Editar perfil
          </Link>
        </div>
      </div>
    </center>
  );
}
