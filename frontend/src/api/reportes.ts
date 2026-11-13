// Conexión del frontend con los reportes (/reportes/...). La escribe la Persona 1.
// Los demás NO editan este archivo: llaman a obtenerReporte('/su-ruta') desde su propia pantalla.
import { api } from './client'

export type Valor = string | number | boolean | null
export type Fila = Record<string, Valor>

export interface ColumnaReporte { clave: string; titulo: string }
export interface DatoReporte { etiqueta: string; valor: string | number }
export interface TablaDatos { titulo: string; columnas: ColumnaReporte[]; filas: Fila[] }
export interface Reporte { titulo: string; resumen: DatoReporte[]; tablas: TablaDatos[] }

// Todos los reportes devuelven la misma forma: título + datos clave + tablas.
export const obtenerReporte = (ruta: string) => api<Reporte>(`/reportes${ruta}`)

export const reportePendientes = (soloVencidos: boolean) =>
  obtenerReporte(`/pendientes?solo_vencidos=${soloVencidos}`)
