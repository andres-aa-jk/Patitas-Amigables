import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';

export default function Entrega() {
  const { solicitudId } = useParams();
  const navigate = useNavigate();
  const [foto, setFoto] = useState(null);
  const [preview, setPreview] = useState(null);
  const [consentimiento, setConsentimiento] = useState(false);
  const [usarUbicacion, setUsarUbicacion] = useState(false);
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  function elegirFoto(e) {
    const f = e.target.files?.[0];
    if (f) {
      setFoto(f);
      setPreview(URL.createObjectURL(f));
    }
  }

  function ubicacion() {
    return new Promise((resolve) => {
      if (!usarUbicacion || !navigator.geolocation) return resolve(null);
      navigator.geolocation.getCurrentPosition(
        (p) => resolve(p.coords),
        () => resolve(null),
        { timeout: 8000 }
      );
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!foto) return setError('Selecciona o toma una foto.');
    setError('');
    setEnviando(true);
    try {
      const coords = await ubicacion();
      const fd = new FormData();
      fd.append('solicitud', solicitudId);
      fd.append('foto', foto);
      fd.append('consentimiento_imagen', consentimiento ? 'true' : 'false');
      if (coords) {
        fd.append('latitud', coords.latitude);
        fd.append('longitud', coords.longitude);
      }
      await api.subirEntrega(fd);
      navigate('/mis-solicitudes', {
        state: { aviso: 'Constancia enviada. Un administrador la validará.' },
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="form-container">
      <h2>Constancia de recogida</h2>
      <p className="form-text">
        Sube una foto tomada al recoger al animal (idealmente donde se vean tú y el animal).
        Solo tú, el refugio y los administradores podrán verla.
      </p>
      <form onSubmit={handleSubmit}>
        {error && <div className="alert alert-danger"><p>{error}</p></div>}
        <div className="form-group">
          <label htmlFor="foto">Foto</label>
          <input id="foto" type="file" accept="image/*" capture="environment" onChange={elegirFoto} required />
          {preview && <img src={preview} alt="Vista previa" style={{ width: 200, borderRadius: 10, marginTop: 8 }} />}
        </div>
        <div className="form-group">
          <label style={{ display: 'flex', gap: '0.5rem' }}>
            <input type="checkbox" style={{ width: 'auto' }} checked={usarUbicacion}
              onChange={(e) => setUsarUbicacion(e.target.checked)} />
            Adjuntar mi ubicación actual (opcional)
          </label>
        </div>
        <div className="form-group">
          <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
            <input type="checkbox" style={{ width: 'auto', marginTop: 4 }} checked={consentimiento}
              onChange={(e) => setConsentimiento(e.target.checked)} required />
            <span>
              Autorizo el tratamiento de esta imagen, que puede mostrar mi rostro, como constancia
              de la entrega (Ley 1581 de 2012). Se conservará solo el tiempo necesario.
            </span>
          </label>
        </div>
        <button type="submit" className="btn" disabled={enviando}>
          {enviando ? 'Enviando...' : 'Enviar constancia'}
        </button>
      </form>
      <p><Link to="/mis-solicitudes">Volver a mis solicitudes</Link></p>
    </div>
  );
}
