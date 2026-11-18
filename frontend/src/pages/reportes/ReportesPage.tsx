import { useState } from 'react'
import ReportePendientes from './ReportePendientes'
import ReporteEquipo from './ReporteEquipo'
import ReporteMensual from './ReporteMensual'
import ReporteUsuario from './ReporteUsuario'
import type { SessionUser } from '../../api/auth'
import './reportes.css'

type Vista = 'pendientes' | 'usuario' | 'equipo' | 'periodo'

const REPORTES: { id: Vista; titulo: string; detalle: string }[] = [
  { id: 'pendientes', titulo: 'Pendientes de devolución', detalle: 'Quién tiene equipos sin devolver y cuántos días de atraso' },
  { id: 'usuario', titulo: 'Reporte de usuario', detalle: 'Préstamos y reservas de una persona' },
  { id: 'equipo', titulo: 'Reporte de equipo', detalle: 'Quién lo tuvo, cuánto tiempo, cómo lo devolvió y sus observaciones' },
  { id: 'periodo', titulo: 'Reporte por periodo', detalle: 'Cómo estuvo el sistema en un mes o en un rango de fechas' },
]

// El administrador ve los 4 reportes. Cualquier otra persona solo ve SU propio reporte de usuario
// (el backend también lo exige: /reportes/usuario/{id} responde 403 si el id no es el suyo).
export default function ReportesPage({ user }: { user: SessionUser }) {
  const [vista, setVista] = useState<Vista>('pendientes')

  if (!user.administrador) {
    return (
      <div className="rep-page">
        <header className="rep-cabecera">
          <h1>Mi reporte</h1>
          <p>Tus préstamos y reservas, con su estado y observaciones.</p>
        </header>
        <ReporteUsuario usuarioId={user.id} />
      </div>
    )
  }

  return (
    <div className="rep-page">
      <header className="rep-cabecera">
        <h1>Reportes</h1>
        <p>Elige un reporte. Se genera con los datos actuales de la base.</p>
      </header>

      <nav className="rep-menu" aria-label="Reportes disponibles">
        {REPORTES.map(r => (
          <button
            key={r.id}
            type="button"
            className={vista === r.id ? 'selected' : ''}
            aria-current={vista === r.id ? 'page' : undefined}
            onClick={() => setVista(r.id)}
          >
            <strong>{r.titulo}</strong>
            <small>{r.detalle}</small>
          </button>
        ))}
      </nav>

      {vista === 'pendientes' ? <ReportePendientes />
        : vista === 'usuario' ? <ReporteUsuario />
        : vista === 'equipo' ? <ReporteEquipo />
        : <ReporteMensual />}
    </div>
  )
}
