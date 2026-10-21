
import { useState } from "react";
import "./prestamo.css";

type EstadoPrestamo =
  | "ACTIVO"
  | "VENCIDO"
  | "DEVUELTO";

type PrestamoVista = {
  id: number;
  usuario: string;
  objeto: string;
  fechaInicio: string;
  fechaFin: string;
  estado: EstadoPrestamo;
};

const datosDemo: PrestamoVista[] = [
  {
    id: 1,
    usuario: "Juan Delgado",
    objeto: "Laptop Dell Latitude",
    fechaInicio: "20/10/2026",
    fechaFin: "25/10/2026",
    estado: "ACTIVO",
  },
  {
    id: 2,
    usuario: "María Ramos",
    objeto: "Proyector Epson",
    fechaInicio: "10/10/2026",
    fechaFin: "15/10/2026",
    estado: "VENCIDO",
  },
  {
    id: 3,
    usuario: "Carlos Pérez",
    objeto: "Cámara Canon",
    fechaInicio: "05/10/2026",
    fechaFin: "08/10/2026",
    estado: "DEVUELTO",
  },
];

export default function PrestamosPage() {
  const [filtro, setFiltro] = useState("TODOS");

  const prestamosFiltrados = datosDemo.filter((p) =>
    filtro === "TODOS" ? true : p.estado === filtro
  );

  return (
    <main className="main prestamos-page">
      <header className="topbar">
        <div>
          <h1>Préstamos</h1>
          <p>Gestiona entregas, plazos y devoluciones de equipos.</p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={() =>
            alert("Aquí conectaremos el formulario de nuevo préstamo.")
          }
        >
          + Nuevo préstamo
        </button>
      </header>

      <section className="prestamos-resumen">
        <article className="prestamo-metrica">
          <span>Préstamos activos</span>
          <strong>
            {datosDemo.filter((p) => p.estado === "ACTIVO").length}
          </strong>
        </article>

        <article className="prestamo-metrica">
          <span>Vencidos</span>
          <strong>
            {datosDemo.filter((p) => p.estado === "VENCIDO").length}
          </strong>
        </article>

        <article className="prestamo-metrica">
          <span>Devueltos</span>
          <strong>
            {datosDemo.filter((p) => p.estado === "DEVUELTO").length}
          </strong>
        </article>

        <article className="prestamo-metrica">
          <span>Total registrado</span>
          <strong>{datosDemo.length}</strong>
        </article>
      </section>

      <section className="panel">
        <div className="panel-header prestamos-cabecera">
          <div>
            <h2>Registro de préstamos</h2>
            <p>Consulta el usuario, el equipo y la fecha límite.</p>
          </div>

          <select
            aria-label="Filtrar por estado"
            value={filtro}
            onChange={(e) => setFiltro(e.target.value)}
          >
            <option value="TODOS">Todos los estados</option>
            <option value="ACTIVO">Activos</option>
            <option value="VENCIDO">Vencidos</option>
            <option value="DEVUELTO">Devueltos</option>
          </select>
        </div>

        <div className="prestamos-tabla">
          <div className="prestamos-fila prestamos-th">
            <span>Usuario</span>
            <span>Equipo</span>
            <span>Fecha de inicio</span>
            <span>Devolución prevista</span>
            <span>Estado</span>
          </div>

          {prestamosFiltrados.map((p) => (
            <div className="prestamos-fila" key={p.id}>
              <span>
                <strong>{p.usuario}</strong>
                <small>Préstamo #{p.id}</small>
              </span>

              <span>{p.objeto}</span>
              <span>{p.fechaInicio}</span>
              <span>{p.fechaFin}</span>

              <span>
                <span
                  className={`prestamo-estado estado-${p.estado.toLowerCase()}`}
                >
                  {p.estado}
                </span>
              </span>
            </div>
          ))}

          {prestamosFiltrados.length === 0 && (
            <p className="hint">No hay préstamos con ese estado.</p>
          )}
        </div>
      </section>
    </main>
  );
}
