import "./App.css";

function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">P</div>
          <div>
            <h2>Préstamos</h2>
            <span>Universidad</span>
          </div>
        </div>

        <nav>
          <button className="nav-item active">
            <span>⌂</span>
            Inicio
          </button>

          <button className="nav-item">
            <span>♙</span>
            Usuarios
          </button>

          <button className="nav-item">
            <span>▣</span>
            Objetos
          </button>

          <button className="nav-item">
            <span>▤</span>
            Préstamos
          </button>

          <button className="nav-item">
            <span>◷</span>
            Reservas
          </button>
        </nav>

        <div className="sidebar-bottom">
          <button className="nav-item">
            <span>⚙</span>
            Configuración
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>Dashboard</h1>
            <p>Gestión de préstamos en equipos</p>
          </div>

          <div className="profile">
            <div className="avatar">A</div>
            <div>
              <strong>Administrador</strong>
              <span>Administrador</span>
            </div>
          </div>
        </header>

        <section className="welcome">
          <div>
            <h2>Bienvenido al sistema 👋</h2>
            <p>
              Administra usuarios, equipos, préstamos y reservas
              desde un solo lugar.
            </p>
          </div>

          <button className="primary-button">
            + Nuevo préstamo
          </button>
        </section>

        <section className="stats">
          <div className="stat-card">
            <div className="stat-icon">▣</div>
            <div>
              <span>Objetos registrados</span>
              <strong>24</strong>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">↗</div>
            <div>
              <span>Préstamos activos</span>
              <strong>8</strong>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">◷</div>
            <div>
              <span>Solicitudes pendientes</span>
              <strong>3</strong>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✓</div>
            <div>
              <span>Usuarios registrados</span>
              <strong>42</strong>
            </div>
          </div>
        </section>

        <section className="content-grid">
          <div className="panel">
            <div className="panel-header">
              <div>
                <h2>Objetos recientes</h2>
                <p>Estado actual del inventario</p>
              </div>

              <button className="link-button">
                Ver todos
              </button>
            </div>

            <div className="table">
              <div className="table-row table-header">
                <span>Objeto</span>
                <span>Categoría</span>
                <span>Estado</span>
              </div>

              <div className="table-row">
                <span>
                  <strong>Laptop Dell Latitude</strong>
                </span>
                <span>Computadora</span>
                <span className="status available">
                  Disponible
                </span>
              </div>

              <div className="table-row">
                <span>
                  <strong>Proyector Epson</strong>
                </span>
                <span>Proyección</span>
                <span className="status borrowed">
                  Prestado
                </span>
              </div>

              <div className="table-row">
                <span>
                  <strong>Cámara Canon</strong>
                </span>
                <span>Multimedia</span>
                <span className="status available">
                  Disponible
                </span>
              </div>

              <div className="table-row">
                <span>
                  <strong>Micrófono inalámbrico</strong>
                </span>
                <span>Audio</span>
                <span className="status reserved">
                  Reservado
                </span>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <h2>Préstamos recientes</h2>
                <p>Últimos movimientos</p>
              </div>
            </div>

            <div className="loan">
              <div className="loan-avatar">JD</div>
              <div className="loan-info">
                <strong>Juan Delgado</strong>
                <span>Laptop Dell</span>
              </div>
              <span className="loan-date">Hoy</span>
            </div>

            <div className="loan">
              <div className="loan-avatar">MR</div>
              <div className="loan-info">
                <strong>María Ramos</strong>
                <span>Proyector Epson</span>
              </div>
              <span className="loan-date">Ayer</span>
            </div>

            <div className="loan">
              <div className="loan-avatar">CP</div>
              <div className="loan-info">
                <strong>Carlos Pérez</strong>
                <span>Cámara Canon</span>
              </div>
              <span className="loan-date">Ayer</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;