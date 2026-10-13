import { createContext, useContext, useEffect, useState } from 'react';
import { api, tokens } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Al cargar la app, si hay token guardado recuperamos el perfil del backend.
  useEffect(() => {
    async function loadUser() {
      if (!tokens.access) {
        setLoading(false);
        return;
      }
      try {
        const data = await api.me();
        setUser(data);
      } catch {
        tokens.clear();
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, []);

  async function login(username, password) {
    try {
      const data = await api.login(username, password);
      tokens.save({ access: data.access, refresh: data.refresh });
      setUser(data.user);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  }

  async function register(payload) {
    try {
      const data = await api.register(payload);
      tokens.save({ access: data.access, refresh: data.refresh });
      setUser(data.user);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  }

  function logout() {
    tokens.clear();
    setUser(null);
  }

  async function updateProfile(payload) {
    try {
      const data = await api.updateMe(payload);
      setUser(data);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  }

  async function changePassword({ oldPassword, newPassword1, newPassword2 }) {
    try {
      await api.changePassword({
        old_password: oldPassword,
        new_password1: newPassword1,
        new_password2: newPassword2,
      });
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  }

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    isAdmin: user?.rol === 'admin',
    login,
    register,
    logout,
    updateProfile,
    changePassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}
