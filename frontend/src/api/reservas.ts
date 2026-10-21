import { api } from "./client";

export type EstadoReserva = "PENDIENTE" | "CONFIRMADA" | "FINALIZADA" | "CANCELADA" | "VENCIDA";

// Es exactamente el JSON que devuelve el backend (reserva_routes.py -> _a_dict)
export interface Reserva {
  id: number;
  usuario_id: number;
  objeto_id: number;
  fecha_reserva: string; // "2026-10-20"
  fecha_inicio: string;
  fecha_fin: string;
  estado: EstadoReserva;
}

// Es exactamente lo que espera el backend (reserva_routes.py -> ReservaCreate)
export interface NuevaReserva {
  usuario_id: number;
  objeto_id: number;
  fecha_inicio: string;
  fecha_fin: string;
}

export type AccionReserva = "confirmar" | "cancelar" | "finalizar";

export const listarReservas = () => api<Reserva[]>("/reservas/");

export const crearReserva = (datos: NuevaReserva) =>
  api<Reserva>("/reservas/", { method: "POST", body: datos });

export const cambiarEstadoReserva = (id: number, accion: AccionReserva) =>
  api<Reserva>(`/reservas/${id}/${accion}`, { method: "POST" });

export const procesarVencidas = () =>
  api<Reserva[]>("/reservas/procesar-vencidas", { method: "POST" });
