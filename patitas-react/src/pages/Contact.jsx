export default function Contact() {
  return (
    <center>
      <div className="container mt-4" style={{ maxWidth: 800, width: '100%' }}>
        <div
          style={{
            background: 'white',
            padding: '1.5rem',
            borderRadius: 12,
            marginTop: '1rem',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}
        >
          <center>
            <h1>Contáctanos</h1>
          </center>
          <p style={{ textAlign: 'center', maxWidth: 720, margin: '0.75rem auto 1.25rem' }}>
            Si quieres contactarnos, elige una de las siguientes opciones. Con gusto te
            atenderemos.
          </p>
          <br />
          <div className="contact-grid" style={{ marginTop: '1rem' }}>
            <div className="contact-card">
              <div className="contact-icon">📸</div>
              <h3>Instagram</h3>
              <p>
                <a
                  href="https://www.instagram.com/patitas_amigables_"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  @patitas_amigables_
                </a>
              </p>
            </div>
            <div className="contact-card">
              <div className="contact-icon">💬</div>
              <h3>WhatsApp</h3>
              <p>
                <a
                  href="https://wa.me/573148283674"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  +57 314 828 3674
                </a>
              </p>
            </div>
            <div className="contact-card">
              <div className="contact-icon">✉️</div>
              <h3>Correo</h3>
              <p>
                <a href="mailto:patitasamigablesz@gmail.com">patitasamigablesz@gmail.com</a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </center>
  );
}
