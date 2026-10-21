import { api } from "./client";

export interface Objeto {
  id: number;
  nombre: string;
  descripcion: string;
  categoria_id: number;
  estado_disponibilidad: "DISPONIBLE" | "PRESTADO" | "RESERVADO" | "NO_DISPONIBLE" | "DADO_DE_BAJA";
  estado_fisico: "BUENO" | "REGULAR" | "DANHADO";
}

export const listarObjetos = () => api<Objeto[]>("/objetos/");
