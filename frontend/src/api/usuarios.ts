import { api } from "./client";

export interface Usuario {
  id: number;
  nombre: string;
  correo: string;
  codigo: string;
  tipo: string;
  estado: "ACTIVO" | "INACTIVO" | "SUSPENDIDO" | null;
  credibilidad: number;
  rol: string | null;
}

// OJO: la ruta termina en "/" porque en el backend está definida como "/usuarios/".
// Sin la barra, FastAPI responde con una redirección (307) y el navegador puede bloquearla.
export const listarUsuarios = () => api<Usuario[]>("/usuarios/");
