import { api } from './client'

export interface SessionUser {
  id: number; nombre: string; correo: string; tipo: string; administrador: boolean
}

export const login = (correo: string, password: string) =>
  api<SessionUser>('/auth/login', { method: 'POST', body: { correo, password } })

export const me = () => api<SessionUser>('/auth/me')
export const logout = () => api('/auth/logout', { method: 'POST' })

export interface RegistroCuenta {
  nombre: string; correo: string; codigo: string
  tipo: 'Estudiante' | 'Profesor' | 'Administrativo'
  password: string
  especialidad?: string; area?: string; cargo?: string
  constancia?: File | null
}

export const register = async (datos: RegistroCuenta) => {
  const fd = new FormData()
  fd.append('nombre', datos.nombre)
  fd.append('correo', datos.correo)
  fd.append('codigo', datos.codigo)
  fd.append('tipo', datos.tipo)
  fd.append('password', datos.password)
  if (datos.especialidad) fd.append('especialidad', datos.especialidad)
  if (datos.area) fd.append('area', datos.area)
  if (datos.cargo) fd.append('cargo', datos.cargo)
  if (datos.constancia) fd.append('constancia', datos.constancia)

  const respuesta = await fetch(`${(await import('./client')).API_URL}/auth/register`, {
    method: 'POST',
    credentials: 'include',
    body: fd, // NO poner Content-Type: el navegador agrega el boundary
  })
  if (!respuesta.ok) {
    const err = await respuesta.json().catch(() => null)
    throw new Error(err?.detail ?? 'No se pudo enviar la solicitud.')
  }
  return respuesta.json() as Promise<{ id: number; mensaje: string; verificado_externo: boolean; advertencia: string }>
}

export interface MiPerfil extends SessionUser {
  codigo: string; credibilidad: number
  carrera: string | null; especialidad: string | null
  departamento: string | null; area: string | null; cargo: string | null
  constancia_matricula: boolean
}

export const obtenerPerfil = () => api<MiPerfil>('/auth/me')
export const guardarPerfil = (datos: { nombre: string; especialidad: string }) =>
  api<MiPerfil>('/auth/me', { method: 'PUT', body: datos })

export const cambiarPassword = (password_actual: string, password_nueva: string) => 
  api<{ mensaje: string }>('/auth/me/password', { 
    method: 'PUT', 
    body: { password_actual, password_nueva } 
  })