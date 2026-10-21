import { useEffect, useState } from "react";
import { listarUsuarios } from "./api/usuarios";
import type { Usuario } from "./api/usuarios";
import { listarObjetos } from "./api/objetos";
import type { Objeto } from "./api/objetos";
import { listarReservas } from "./api/reservas";
import type { Reserva } from "./api/reservas";
import ReservasPage from "./pages/reservas/ReservasPage";
import CatalogoPage from "./pages/catalogo/CatalogoPage";
import UsuarioPage from "./usuario/UsuarioPage";
import "./Workspace.css";

type Page = "Resumen" | "Usuarios" | "Equipos" | "Reservas" | "Préstamos";

export default function Workspace({ logout }: { logout: () => void }) {
  const [page, setPage] = useState<Page>("Resumen");
  const [users, setUsers] = useState<Usuario[]>([]);
  const [objects, setObjects] = useState<Objeto[]>([]);
  const [reservations, setReservations] = useState<Reserva[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [u, o, r] = await Promise.all([
        listarUsuarios(),
        listarObjetos(),
        listarReservas(),
      ]);
      setUsers(u);
      setObjects(o);
      setReservations(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar los datos");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="workspace">
      <aside className="workspace-nav">
        <img src="/epcc.jpg" alt="EPCC UNSA" />
        <strong>Sistema de préstamos</strong>
        <small>Gestión de recursos · EPCC</small>
        <nav>
          {(["Resumen", "Usuarios", "Equipos", "Reservas", "Préstamos"] as Page[]).map((p) => (
            <button
              key={p}
              className={page === p ? "selected" : ""}
              onClick={() => {
                setPage(p);
                void load();
              }}
            >
              {p}
            </button>
          ))}
        </nav>
        <button onClick={logout}>Salir de demostración</button>
      </aside>

      <main className="workspace-content">
        <div className="workspace-banner">
          Acceso de demostración · Los cambios en usuarios y reservas se guardan en la base de datos.
        </div>

        {page === "Usuarios" ? (
          <UsuarioPage />
        ) : page === "Equipos" ? (
          <CatalogoPage />
        ) : page === "Reservas" ? (
          <ReservasPage />
        ) : (
          <>
            <header className="topbar">
              <div>
                <h1>{page}</h1>
                <p>Escuela Profesional de Ciencia de la Computación</p>
              </div>
              <button className="primary-button" disabled={loading} onClick={() => void load()}>
                {loading ? "Cargando…" : "Actualizar"}
              </button>
            </header>

            {error && <p className="alert alert-error" role="alert">{error}</p>}

            {page === "Resumen" && !error && (
              <>
                <section className="workspace-stats">
                  {[
                    ["Usuarios registrados", users.length],
                    ["Equipos registrados", objects.length],
                    ["Equipos disponibles", objects.filter((o) => o.estado_disponibilidad === "DISPONIBLE").length],
                    ["Reservas", reservations.length],
                  ].map(([name, count]) => (
                    <article className="panel" key={String(name)}>
                      <span>{name}</span>
                      <strong>{loading ? "…" : count}</strong>
                    </article>
                  ))}
                </section>
                <section className="panel workspace-message">
                  <h2>Gestiona los recursos de la escuela</h2>
                  <p>Consulta usuarios y equipos registrados, o crea y administra reservas.</p>
                  <button className="primary-button" onClick={() => setPage("Reservas")}>
                    Administrar reservas →
                  </button>
                </section>
              </>
            )}

            {page === "Préstamos" && (
              <section className="panel workspace-message">
                <h2>Módulo pendiente de integración</h2>
                <p>
                  El backend actual contiene las entidades de préstamos, pero todavía no implementa
                  su almacenamiento ni sus rutas.
                </p>
                <button className="primary-button" onClick={() => setPage("Reservas")}>
                  Ir a reservas
                </button>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}