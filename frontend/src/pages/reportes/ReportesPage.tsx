import { useState } from 'react'
import ReportePendientes from './ReportePendientes'
import ReporteEquipo from './ReporteEquipo'
import ReporteMensual from './ReporteMensual'
import ReporteUsuario from './ReporteUsuario'
import './reportes.css'

type Vista = 'pendientes' | 'usuario' | 'equipo' | 'mensual'

const REPORTES: { id: Vista; titulo: string; detalle: string }[] = [
  { id: 'pendientes', titulo: 'Pendientes de devolución', detalle: 'Quién tiene equipos sin devolver y cuántos días de atraso' },
  { id: 'usuario', titulo: 'Reporte de usuario', detalle: 'Préstamos y reservas de una persona' },
  { id: 'equipo', titulo: 'Reporte de equipo', detalle: 'Quién lo tuvo, cuánto tiempo y cómo lo devolvió' },
  { id: 'mensual', titulo: 'Reporte mensual', detalle: 'Préstamos, devoluciones y reservas de un mes' },
]

// Solo la ve el administrador (Workspace oculta el menú y el backend responde 403 a los demás).
export default function ReportesPage() {
  const [vista, setVista] = useState<Vista>('pendientes')

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
