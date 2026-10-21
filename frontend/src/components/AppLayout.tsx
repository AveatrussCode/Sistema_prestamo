
import { NavLink, Outlet } from "react-router-dom";

export default function AppLayout() {
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
          <NavLink to="/" end className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }>
            <span>⌂</span>
            Inicio
          </NavLink>

          <button className="nav-item" type="button">
            <span>♙</span>
            Usuarios
          </button>

          <NavLink to="/catalogo" className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }>
            <span>▣</span>
            Objetos
          </NavLink>

          <button className="nav-item" type="button">
            <span>▤</span>
            Préstamos
          </button>

          <NavLink to="/reservas" className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }>
            <span>◷</span>
            Reservas
          </NavLink>
        </nav>

        <div className="sidebar-bottom">
          <button className="nav-item" type="button">
            <span>⚙</span>
            Configuración
          </button>
        </div>
      </aside>

      <Outlet />
    </div>
  );
}
