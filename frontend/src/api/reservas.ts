import { api } from "./client";

export type EstadoReserva = "PENDIENTE" | "CONFIRMADA" | "FINALIZADA" | "CANCELADA" | "VENCIDA";

export interface Reserva {
  id: number;
  usuario_id: number;
  objeto_id: number;
  fecha_reserva: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado: EstadoReserva;
  objeto_tiene_imagen?: boolean; // <--- NUEVO CAMPO
}

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