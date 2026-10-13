import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProfileEdit() {
  const { user, updateProfile, changePassword } = useAuth();
  const navigate = useNavigate();

  const [profileForm, setProfileForm] = useState({
    username: user?.username || '',
    email: user?.email || '',
    direccion: user?.direccion || '',
    numero: user?.numero || '',
  });
  const [profileError, setProfileError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');

  const [pwdForm, setPwdForm] = useState({
    oldPassword: '',
    newPassword1: '',
    newPassword2: '',
  });
  const [pwdError, setPwdError] = useState('');
  const [pwdSuccess, setPwdSuccess] = useState('');

  function handleProfileChange(e) {
    setProfileForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleProfileSubmit(e) {
    e.preventDefault();
    const result = await updateProfile(profileForm);
    if (result.ok) {
      setProfileSuccess('Perfil actualizado correctamente.');
      setProfileError('');
      setTimeout(() => navigate('/perfil'), 800);
    } else {
      setProfileError(result.error);
      setProfileSuccess('');
    }
  }

  function handlePwdChange(e) {
    setPwdForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handlePwdSubmit(e) {
    e.preventDefault();
    const result = await changePassword(pwdForm);
    if (result.ok) {
      setPwdSuccess('Contraseña actualizada correctamente.');
      setPwdError('');
      setPwdForm({ oldPassword: '', newPassword1: '', newPassword2: '' });
    } else {
      setPwdError(result.error);
      setPwdSuccess('');
    }
  }

  return (
    <center>
      <div style={{ maxWidth: 800, width: '100%' }}>
        <div className="form-container">
          <h2>Editar perfil</h2>
          <form onSubmit={handleProfileSubmit}>
            {profileError && (
              <div className="alert alert-danger">
                <p>{profileError}</p>
              </div>
            )}
            {profileSuccess && (
              <div className="alert alert-success">
                <p>{profileSuccess}</p>
              </div>
            )}
            <div className="form-group">
              <label htmlFor="username">Nombre de usuario:</label>
              <input
                id="username"
                name="username"
                className="form-control"
                type="text"
                value={profileForm.username}
                onChange={handleProfileChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">Correo electrónico:</label>
              <input
                id="email"
                name="email"
                className="form-control"
                type="email"
                value={profileForm.email}
                onChange={handleProfileChange}
              />
            </div>
            <div className="form-group">
              <label htmlFor="direccion">Dirección:</label>
              <textarea
                id="direccion"
                name="direccion"
                className="form-control"
                rows={3}
                value={profileForm.direccion}
                onChange={handleProfileChange}
              />
            </div>
            <div className="form-group">
              <label htmlFor="numero">Número de teléfono:</label>
              <input
                id="numero"
                name="numero"
                className="form-control"
                type="text"
                maxLength={20}
                value={profileForm.numero}
                onChange={handleProfileChange}
              />
            </div>
            <button type="submit" className="btn">
              Guardar cambios
            </button>
          </form>
        </div>

        <div className="form-container" style={{ marginTop: '1rem' }}>
          <h2>Cambiar contraseña</h2>
          <form onSubmit={handlePwdSubmit}>
            {pwdError && (
              <div className="alert alert-danger">
                <p>{pwdError}</p>
              </div>
            )}
            {pwdSuccess && (
              <div className="alert alert-success">
                <p>{pwdSuccess}</p>
              </div>
            )}
            <div className="form-group">
              <label htmlFor="oldPassword">Contraseña actual:</label>
              <input
                id="oldPassword"
                name="oldPassword"
                className="form-control"
                type="password"
                value={pwdForm.oldPassword}
                onChange={handlePwdChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="newPassword1">Nueva contraseña:</label>
              <input
                id="newPassword1"
                name="newPassword1"
                className="form-control"
                type="password"
                value={pwdForm.newPassword1}
                onChange={handlePwdChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="newPassword2">Confirmar nueva contraseña:</label>
              <input
                id="newPassword2"
                name="newPassword2"
                className="form-control"
                type="password"
                value={pwdForm.newPassword2}
                onChange={handlePwdChange}
                required
              />
            </div>
            <button type="submit" className="btn">
              Cambiar contraseña
            </button>
          </form>
        </div>
      </div>
    </center>
  );
}
