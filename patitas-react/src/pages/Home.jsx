import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useAnimals } from '../context/AnimalsContext';
import PetsMap from '../components/PetsMap';

export default function Home() {
  const { isAuthenticated } = useAuth();
  const { animales, loading, error, ESPECIES } = useAnimals();
  const navigate = useNavigate();

  function adoptar(animal) {
    navigate(isAuthenticated ? `/adoptar/${animal.id}` : '/login');
  }

  return (
    <div className="dashboard-container">
      <center>
        <h1>MASCOTAS EN BUSCA DE HOGAR</h1>
      </center>

      {error && (
        <div className="messages">
          <div className="message">
            No se pudo conectar con el servidor: {error}. ¿Está corriendo Django en el
            puerto 8000?
          </div>
        </div>
      )}

      <PetsMap
        animales={animales}
        especieLabels={ESPECIES}
        isAuthenticated={isAuthenticated}
        onAdopt={adoptar}
      />

      {loading ? (
        <center>
          <div className="empty-state">
            <h2>Cargando mascotas...</h2>
          </div>
        </center>
      ) : animales.length > 0 ? (
        <div className="pets-grid">
          {animales.map((animal) => (
            <div className="pet-card" key={animal.id}>
              <div className="pet-image">
                <img
                  src={animal.foto_url || '/images/paw-placeholder.svg'}
                  alt={animal.nombre || 'Mascota'}
                  onError={(e) => {
                    e.currentTarget.src = '/images/paw-placeholder.svg';
                  }}
                />
              </div>
              <div className="pet-info">
                <h3>{animal.nombre || 'Sin nombre'}</h3>
                <p className="pet-description">
                  {(animal.descripcion || '').slice(0, 100)}
                </p>
                <div className="pet-details">
                  {animal.edad != null && (
                    <span>
                      <i className="fas fa-birthday-cake"></i> {animal.edad} años
                    </span>
                  )}
                  <span>
                    <i className="fas fa-paw"></i>{' '}
                    {animal.especie_display || ESPECIES[animal.especie]}
                  </span>
                  <span>
                    <i className="fas fa-heartbeat"></i>{' '}
                    {animal.estado_salud_display || animal.estado_salud}
                  </span>
                </div>
                <button type="button" className="btn" onClick={() => adoptar(animal)}>
                  {isAuthenticated ? 'Adoptar' : 'Inicia sesión para adoptar'}
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <center>
          <div className="empty-state">
            <img src="/images/logo.png" alt="No hay mascotas" />
            <h2>No hay mascotas registradas</h2>
            <p>Actualmente no hay mascotas buscando hogar. ¡Vuelve pronto!</p>
            {isAuthenticated ? (
              <Link to="/registrar-animal" className="btn">
                Registrar una mascota
              </Link>
            ) : (
              <Link to="/login" className="btn">
                Iniciar sesión para registrar
              </Link>
            )}
          </div>
        </center>
      )}
    </div>
  );
}
