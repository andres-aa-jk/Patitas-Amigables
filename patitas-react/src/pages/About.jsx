export default function About() {
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
          <p>
            <img
              src="/images/fondo2.jpg"
              alt="fondo_2"
              style={{ maxWidth: '100%', height: 'auto' }}
            />
          </p>
          <p>
            <center>
              <h1>Acerca de Patitas Amigables</h1>
            </center>
          </p>
          <br />
          <div className="row">
            <div className="col-12">
              <p>🪐 VISIÓN</p>
              <p>
                Ser la plataforma digital líder en Mosquera y la región, reconocida por
                transformar la manera en que las comunidades se relacionan con los animales en
                situación de refugio, promoviendo una cultura de empatía, adopción responsable y
                bienestar animal sostenible.
              </p>
              <br />
              <hr />
              <br />
              <p>🎯 Misión</p>
              <p>
                Brindar una solución innovadora mediante un sistema web georreferenciado que
                conecte refugios de animales con adoptantes potenciales, facilite el proceso de
                adopción responsable y ofrezca acompañamiento educativo, contribuyendo así a
                reducir el abandono animal y mejorar la calidad de vida de los animales
                rescatados.
              </p>
              <br />
              <p>
                Patitas Amigables es una plataforma dedicada a conectar mascotas en busca de
                hogar con familias amorosas.
              </p>
            </div>
          </div>
        </div>
      </div>
    </center>
  );
}
