import { api } from './client'

export interface Movimiento {
  id: number; tipo: string; puntos: number; valor_antes: number; valor_despues: number
  motivo: string; estado: string; fecha: string; por_el_sistema: boolean
}
export interface MiCredibilidad {
  valor: number; tope: number; porcentaje: number; nivel: string; nivel_etiqueta: string
  limites: { puede_reservar: boolean; max_dias: number; max_equipos: number; anticipacion_dias: number }
  movimientos: Movimiento[]
}
export const miCredibilidad = () => api<MiCredibilidad>('/credibilidad/mia')