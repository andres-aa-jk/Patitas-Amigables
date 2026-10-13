import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './styles/global.css';
import './styles/forms.css';
import './styles/map.css';
import App from './App.jsx';
import { AuthProvider } from './context/AuthContext';
import { AnimalsProvider } from './context/AnimalsContext';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <AnimalsProvider>
          <App />
        </AnimalsProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
