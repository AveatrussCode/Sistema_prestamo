import { api } from './client'
export interface SessionUser { id: number; nombre: string; correo: string; tipo: string; administrador: boolean }
export const login = (correo: string, password: string) => api<SessionUser>('/auth/login', {method:'POST',body:{correo,password}})
export const me = () => api<SessionUser>('/auth/me')
export const logout = () => api('/auth/logout', {method:'POST'})
export interface RegistroCuenta { nombre: string; correo: string; codigo: string; tipo: 'Estudiante' | 'Profesor'; password: string; especialidad?: string }
export const register = (datos: RegistroCuenta) => api<{ id: number; mensaje: string }>('/auth/register', {method:'POST',body:datos})
export interface MiPerfil extends SessionUser { codigo: string; credibilidad: number; carrera: string | null; especialidad: string | null; departamento: string | null; area: string | null; cargo: string | null; constancia_matricula: boolean }
export const obtenerPerfil = () => api<MiPerfil>('/auth/me')
export const guardarPerfil = (datos: {nombre: string; especialidad: string}) => api<MiPerfil>('/auth/me', {method:'PUT',body:datos})
