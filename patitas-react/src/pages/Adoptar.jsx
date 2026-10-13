import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';

const inicial = {
  motivo: '',
  tipo_vivienda: '',
  tiene_otras_mascotas: false,
  experiencia: '',
  acepta_visita: false,
};

export default function Adoptar() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [animal, setAnimal] = useState(null);
  const [form, setForm] = useState(inicial);
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    api.getAnimal(id).then(setAnimal).catch((e) => setError(e.message));
  }, [id]);

  function handleChange(e) {
    const { name, type, checked, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setEnviando(true);
    try {
      await api.crearSolicitud({ ...form, animal_id: id });
      navigate('/mis-solicitudes', {
        state: { aviso: 'Solicitud enviada. Un administrador la revisará.' },
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  if (!animal && !error) return <center><div className="empty-state"><h2>Cargando...</h2></div></center>;

  return (
    <div className="form-container">
      <h2>Solicitud de adopción{animal ? `: ${animal.nombre || animal.especie_display}` : ''}</h2>
      {animal?.foto_url && (
        <img src={animal.foto_url} alt={animal.nombre || 'Animal'} style={{ width: 160, borderRadius: 12 }} />
      )}
      <form onSubmit={handleSubmit}>
        {error && <div className="alert alert-danger"><p>{error}</p></div>}
        <div className="form-group">
          <label htmlFor="motivo">¿Por qué quieres adoptar? (mínimo 20 caracteres)</label>
          <textarea id="motivo" name="motivo" className="form-control" rows={4}
            value={form.motivo} onChange={handleChange} required />
        </div>
        <div className="form-group">
          <label htmlFor="tipo_vivienda">Tipo de vivienda</label>
          <select id="tipo_vivienda" name="tipo_vivienda" className="form-control"
            value={form.tipo_vivienda} onChange={handleChange} required>
            <option value="">Selecciona...</option>
            <option>Casa con patio</option>
            <option>Casa sin patio</option>
            <option>Apartamento</option>
            <option>Finca o lote</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="experiencia">Experiencia con animales (opcional)</label>
          <textarea id="experiencia" name="experiencia" className="form-control" rows={3}
            value={form.experiencia} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label style={{ display: 'flex', gap: '0.5rem' }}>
            <input type="checkbox" name="tiene_otras_mascotas" style={{ width: 'auto' }}
              checked={form.tiene_otras_mascotas} onChange={handleChange} />
            Tengo otras mascotas en casa
          </label>
        </div>
        <div className="form-group">
          <label style={{ display: 'flex', gap: '0.5rem' }}>
            <input type="checkbox" name="acepta_visita" style={{ width: 'auto' }}
              checked={form.acepta_visita} onChange={handleChange} required />
            Acepto una visita de verificación del refugio
          </label>
        </div>
        <p className="form-text">
          Enviar la solicitud no garantiza la adopción: un administrador la revisará.
        </p>
        <button type="submit" className="btn" disabled={enviando}>
          {enviando ? 'Enviando...' : 'Enviar solicitud'}
        </button>
      </form>
      <p><Link to="/">Volver al mapa</Link></p>
    </div>
  );
}
