import { api } from "./client";

export type EstadoDisponibilidad =
  | "DISPONIBLE"
  | "PRESTADO"
  | "RESERVADO"
  | "NO_DISPONIBLE"
  | "DADO_DE_BAJA";

export type EstadoFisico = "BUENO" | "REGULAR" | "DANHADO";

export interface Objeto {
  id: number;
  nombre: string;
  descripcion: string;
  categoria_id: number;
  estado_disponibilidad: EstadoDisponibilidad;
  estado_fisico: EstadoFisico;
}

export interface Categoria {
  id: number;
  nombre: string;
  descripcion: string;
}

export interface FiltrosObjetos {
  categoria_id?: number;
  estado?: EstadoDisponibilidad;
  busqueda?: string;
  solo_disponibles?: boolean;
}

export const listarObjetos = (filtros: FiltrosObjetos = {}) => {
  const params = new URLSearchParams();
  if (filtros.categoria_id !== undefined) params.set("categoria_id", String(filtros.categoria_id));
  if (filtros.estado) params.set("estado", filtros.estado);
  if (filtros.busqueda) params.set("busqueda", filtros.busqueda);
  if (filtros.solo_disponibles) params.set("solo_disponibles", "true");
  const qs = params.toString();
  return api<Objeto[]>(`/objetos/${qs ? `?${qs}` : ""}`);
};

export const listarCategorias = () => api<Categoria[]>("/categorias/");
export type DatosObjeto = Omit<Objeto, 'id'>;
export const crearObjeto = (body: DatosObjeto) => api<Objeto>('/objetos/', { method: 'POST', body });
export const editarObjeto = (id: number, body: DatosObjeto) => api<Objeto>(`/objetos/${id}`, { method: 'PUT', body });
export const crearCategoria = (nombre: string) => api<Categoria>('/categorias/', { method: 'POST', body: { nombre } });
