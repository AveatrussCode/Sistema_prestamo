import { useCallback, useEffect, useState } from 'react'
import { reportePendientes } from '../../api/reportes'
import type { Reporte } from '../../api/reportes'
import ReporteVista from './ReporteVista'
import './reportes.css'

// Reporte de la Persona 1: equipos que siguen prestados y cuántos días de atraso llevan.
export default function ReportePendientes() {
  const [soloVencidos, setSoloVencidos] = useState(false)
  const [reporte, setReporte] = useState<Reporte | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const cargar = useCallback(() => {
    return reportePendientes(soloVencidos)
      .then(r => { setReporte(r); setError('') })
      .catch((e: unknown) => { setError(e instanceof Error ? e.message : 'No se pudo generar el reporte.') })
      .finally(() => setLoading(false))
  }, [soloVencidos])

  useEffect(() => { void cargar() }, [cargar])

  return (
    <div className="rep-contenido" aria-busy={loading}>
      <div className="rep-filtros">
        <label>
          <input
            type="checkbox"
            checked={soloVencidos}
            onChange={e => { setLoading(true); setSoloVencidos(e.target.checked) }}
          />
          Mostrar solo vencidos
        </label>
        <button type="button" className="rep-boton" disabled={loading} onClick={() => { setLoading(true); void cargar() }}>
          {loading ? 'Actualizando…' : 'Actualizar'}
        </button>
      </div>

      {error && <p className="alert alert-error" role="alert">{error}</p>}
      {loading && !reporte && <p className="rep-vacio" role="status">Generando reporte…</p>}
      {reporte && <ReporteVista reporte={reporte} />}
    </div>
  )
}
