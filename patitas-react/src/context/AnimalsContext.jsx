import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';

const AnimalsContext = createContext(null);

const ESPECIES = {
  perro: 'Perro',
  gato: 'Gato',
  conejo: 'Conejo',
  ave: 'Ave',
};

const ESTADOS_SALUD = {
  saludable: 'Saludable',
  lesionado: 'Lesionado',
  enfermo: 'Enfermo',
  desnutrido: 'Desnutrido',
};

export function AnimalsProvider({ children }) {
  const [animales, setAnimales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchAnimales = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listAnimales();
      // DRF puede devolver una lista o un objeto paginado {results: [...]}
      setAnimales(Array.isArray(data) ? data : data.results || []);
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnimales();
  }, [fetchAnimales]);

  /**
   * Crea un animal. Se envía como FormData porque incluye la foto.
   * data = { nombre, especie, raza, edad, estado_salud, descripcion, latitud, longitud, foto (File) }
   */
  async function addAnimal(data) {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value === null || value === undefined || value === '') return;
      formData.append(key, value);
    });

    try {
      const nuevo = await api.createAnimal(formData);
      // Los animales de usuarios quedan en revisión: solo se muestran si ya están aprobados.
      if (nuevo.estado_publicacion === 'aprobado') setAnimales((prev) => [nuevo, ...prev]);
      return { ok: true, animal: nuevo };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  }

  async function removeAnimal(id) {
    try {
      await api.deleteAnimal(id);
      setAnimales((prev) => prev.filter((a) => a.id !== id));
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  }

  return (
    <AnimalsContext.Provider
      value={{
        animales,
        loading,
        error,
        fetchAnimales,
        addAnimal,
        removeAnimal,
        ESPECIES,
        ESTADOS_SALUD,
      }}
    >
      {children}
    </AnimalsContext.Provider>
  );
}

export function useAnimals() {
  const ctx = useContext(AnimalsContext);
  if (!ctx) throw new Error('useAnimals debe usarse dentro de AnimalsProvider');
  return ctx;
}
