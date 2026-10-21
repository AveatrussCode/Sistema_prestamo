import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { listarObjetos } from "../../api/objetos";
import type { Objeto } from "../../api/objetos";
import { listarUsuarios } from "../../api/usuarios";
import type { Usuario } from "../../api/usuarios";
import { cambiarEstadoReserva, crearReserva, listarReservas, procesarVencidas } from "../../api/reservas";
import type { AccionReserva, Reserva } from "../../api/reservas";
import "./reservas.css";

const mensajeDe = (e: unknown) => (e instanceof Error ? e.message : "Ocurrió un error desconocido");

// "2026-11-03" -> "03/11/2026". Se separa el texto a mano (NO con new Date) para evitar
// el clásico bug de zona horaria que muestra el día anterior.
const formatear = (fecha: string) => {
  const [anio, mes, dia] = fecha.split("-");
  return `${dia}/${mes}/${anio}`;
};

// Fecha de hoy en formato YYYY-MM-DD usando la zona horaria local ("sv-SE" da ese formato).
const hoyLocal = () => new Date().toLocaleDateString("sv-SE");

export default function ReservasPage() {
  // ---- 1) Estado: todo lo que la pantalla "recuerda" ----
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [objetos, setObjetos] = useState<Objeto[]>([]);
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  // Campos del formulario (los <select>/<input> siempre manejan texto)
  const [usuarioId, setUsuarioId] = useState("");
  const [objetoId, setObjetoId] = useState("");
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [enviando, setEnviando] = useState(false);

  // ---- 2) Leer datos del backend ----
  const cargarTodo = useCallback(async () => {
    try {
      const [u, o, r] = await Promise.all([listarUsuarios(), listarObjetos(), listarReservas()]);
      setUsuarios(u);
      setObjetos(o);
      setReservas(r);
    } catch (e) {
      setError(mensajeDe(e));
    } finally {
      setCargando(false);
    }
  }, []);

  // Se ejecuta una vez al abrir la pantalla
  useEffect(() => {
    void cargarTodo();
  }, [cargarTodo]);

  // ---- 3) Acciones del usuario ----
  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); // evita que el navegador recargue la página
    setError(null);
    setMensaje(null);
    setEnviando(true);
    try {
      await crearReserva({
        usuario_id: Number(usuarioId),
        objeto_id: Number(objetoId),
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
      });
      setMensaje("Reserva creada correctamente.");
      setFechaInicio("");
      setFechaFin("");
      await cargarTodo(); // volver a leer la lista para ver la reserva nueva
    } catch (e) {
      setError(mensajeDe(e)); // aquí llegan los mensajes de las reglas: "ya está reservado...", etc.
    } finally {
      setEnviando(false);
    }
  }

  async function cambiarEstado(id: number, accion: AccionReserva) {
    setError(null);
    setMensaje(null);
    try {
      await cambiarEstadoReserva(id, accion);
      await cargarTodo();
    } catch (e) {
      setError(mensajeDe(e));
    }
  }

  async function marcarVencidas() {
    setError(null);
    try {
      const cambiadas = await procesarVencidas();
      setMensaje(`Reservas marcadas como vencidas: ${cambiadas.length}`);
      await cargarTodo();
    } catch (e) {
      setError(mensajeDe(e));
    }
  }

  // ---- 4) Pequeños ayudantes para mostrar nombres en vez de números ----
  const nombreUsuario = (id: number) => usuarios.find((u) => u.id === id)?.nombre ?? `Usuario #${id}`;
  const nombreObjeto = (id: number) => objetos.find((o) => o.id === id)?.nombre ?? `Objeto #${id}`;

  const usuariosActivos = usuarios.filter((u) => u.estado === "ACTIVO");
  const objetosReservables = objetos.filter((o) => o.estado_disponibilidad !== "DADO_DE_BAJA");

  // ---- 5) Lo que se dibuja ----
  return (
    <div className="page-reservas">
      <header className="topbar">
        <div>
          <h1>Reservas</h1>
          <p>Reserva objetos para unas fechas y administra su estado</p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}
      {mensaje && <div className="alert alert-ok">{mensaje}</div>}

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Nueva reserva</h2>
            <p>Las fechas no pueden cruzarse con otra reserva activa del mismo objeto</p>
          </div>
        </div>

        {usuariosActivos.length === 0 || objetosReservables.length === 0 ? (
          <p className="hint">
            {cargando
              ? "Cargando..."
              : "Todavía no hay usuarios activos u objetos. Regístralos, o activa los datos de prueba con SEED_DEMO=true en el archivo .env y reinicia el backend."}
          </p>
        ) : (
          <form className="form-grid" onSubmit={enviar}>
            <label className="field">
              Usuario
              <select value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)} required>
                <option value="">Selecciona...</option>
                {usuariosActivos.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              Objeto
              <select value={objetoId} onChange={(e) => setObjetoId(e.target.value)} required>
                <option value="">Selecciona...</option>
                {objetosReservables.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.nombre}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              Desde
              <input
                type="date"
                value={fechaInicio}
                min={hoyLocal()}
                onChange={(e) => setFechaInicio(e.target.value)}
                required
              />
            </label>

            <label className="field">
              Hasta
              <input
                type="date"
                value={fechaFin}
                min={fechaInicio || hoyLocal()}
                onChange={(e) => setFechaFin(e.target.value)}
                required
              />
            </label>

            <button className="btn" type="submit" disabled={enviando}>
              {enviando ? "Guardando..." : "Reservar"}
            </button>
          </form>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Reservas</h2>
            <p>{reservas.length} registradas</p>
          </div>
          <button className="btn btn-small btn-ghost" onClick={marcarVencidas}>
            Marcar vencidas
          </button>
        </div>

        <div className="reservas-row table-header">
          <span>Usuario</span>
          <span>Objeto</span>
          <span>Desde</span>
          <span>Hasta</span>
          <span>Estado</span>
          <span>Acciones</span>
        </div>

        {reservas.length === 0 && <p className="hint">{cargando ? "Cargando..." : "No hay reservas todavía."}</p>}

        {reservas.map((r) => (
          <div className="reservas-row" key={r.id}>
            <span>
              <strong>{nombreUsuario(r.usuario_id)}</strong>
            </span>
            <span>{nombreObjeto(r.objeto_id)}</span>
            <span>{formatear(r.fecha_inicio)}</span>
            <span>{formatear(r.fecha_fin)}</span>
            <span className={`status estado-${r.estado.toLowerCase()}`}>{r.estado}</span>
            <span className="reservas-acciones">
              {r.estado === "PENDIENTE" && (
                <button className="btn btn-small" onClick={() => cambiarEstado(r.id, "confirmar")}>
                  Confirmar
                </button>
              )}
              {r.estado === "CONFIRMADA" && (
                <button className="btn btn-small" onClick={() => cambiarEstado(r.id, "finalizar")}>
                  Finalizar
                </button>
              )}
              {(r.estado === "PENDIENTE" || r.estado === "CONFIRMADA") && (
                <button className="btn btn-small btn-danger" onClick={() => cambiarEstado(r.id, "cancelar")}>
                  Cancelar
                </button>
              )}
            </span>
          </div>
        ))}
      </section>
    </div>
  );
}
