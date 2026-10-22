import { API_URL } from '../api/client'
import { api } from '../api/client'
import type { Usuario } from '../api/usuarios'
export { listarUsuarios } from '../api/usuarios'
export type { Usuario } from '../api/usuarios'
export type TipoUsuario = 'Estudiante' | 'Profesor' | 'Administrativo'
export type EstadoUsuario = NonNullable<Usuario['estado']>
export interface NuevoUsuario {
  password?: string;
  nombre: string; correo: string; codigo: string; tipo: TipoUsuario;
  carrera?: string; matricula?: string; departamento?: string;
  especialidad?: string; area?: string; cargo?: string;
}
export interface Rol { id: number; nombre: string; nivel: string; permisos: string[] }
export const crearUsuario = (datos: NuevoUsuario) => api<{ id: number }>('/usuarios/', { method: 'POST', body: datos })
export const editarUsuario = (id: number, datos: { nombre: string; correo: string }) => api(`/usuarios/${id}`, { method: 'PUT', body: datos })
export const cambiarEstado = (id: number, estado: EstadoUsuario) => api(`/usuarios/${id}/estado`, { method: 'PUT', body: { estado } })
export const eliminarUsuario = (id: number) => api(`/usuarios/${id}`, { method: 'DELETE' })
export const listarRoles = () => api<Rol[]>('/roles/')
export const asignarRol = (id: number, id_rol: number) => api(`/usuarios/${id}/rol`, { method: 'PUT', body: { id_rol } })
export const ajustarCredibilidad = (id: number, valor: number, motivo: string) => api(`/usuarios/${id}/credibilidad`, { method: 'PUT', body: { valor, motivo } })

export const constanciaUrl = (id: number) => `${API_URL}/usuarios/${id}/constancia-matricula`
export async function subirConstancia(id: number, archivo: File) {
  const respuesta = await fetch(constanciaUrl(id), { method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/pdf' }, body: archivo })
  if (!respuesta.ok) {
    const error = await respuesta.json().catch(() => null)
    throw new Error(error?.detail ?? 'No se pudo subir la constancia. Intenta nuevamente.')
  }
}
