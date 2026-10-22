import { api } from './client'
export interface Prestamo {
  id: number; reserva_id: number; usuario_id: number; objeto_id: number; entregado_por: number;
  usuario: string; equipo: string; fecha_inicio: string; fecha_devolucion_prevista: string;
  fecha_devolucion_real: string | null; estado: 'ACTIVO' | 'VENCIDO' | 'DEVUELTO' | 'CANCELADO';
  observaciones_entrega: string;
  devolucion: { fecha: string; estado_fisico: 'BUENO' | 'REGULAR' | 'DANHADO'; observaciones: string; recibido_por: number; fuera_de_plazo: boolean } | null;
}
export const listarPrestamos = () => api<Prestamo[]>('/prestamos/')
export const entregarEquipo = (reserva_id: number, observaciones: string) => api<Prestamo>('/prestamos/', { method: 'POST', body: { reserva_id, observaciones } })
export const devolverEquipo = (id: number, estado_fisico: string, observaciones: string) => api<Prestamo>(`/prestamos/${id}/devolucion`, { method: 'POST', body: { estado_fisico, observaciones } })
