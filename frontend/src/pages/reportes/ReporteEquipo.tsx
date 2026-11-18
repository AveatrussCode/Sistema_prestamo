import { useCallback, useEffect, useRef, useState } from 'react'
import { obtenerReporte } from '../../api/reportes'
import type { Reporte } from '../../api/reportes'
import { listarObjetos } from '../../api/objetos'
import type { Objeto } from '../../api/objetos'
import ReporteVista from './ReporteVista'
import './reportes.css'

// Reporte de equipo: por qué manos pasó, cuánto tiempo, cómo lo devolvieron y qué se observó.
// El administrador elige el equipo en una lista (incluye los dados de baja, para poder revisar su historia).
export default function ReporteEquipo() {
  const [equipos, setEquipos] = useState<Objeto[]>([])
  const [elegido, setElegido] = useState<number | null>(null)
  const [reporte, setReporte] = useState<Reporte | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const peticion = useRef(0) // si el admin cambia de equipo rápido, solo vale la última respuesta

  // 1) La lista de equipos para poder elegir.
  useEffect(() => {
    Promise.all([listarObjetos(), listarObjetos({ estado: 'DADO_DE_BAJA' })])
      .then(([activos, bajas]) => {
        const porId = new Map<number, Objeto>()
        for (const o of [...activos, ...bajas]) porId.set(o.id, o)
        setEquipos([...porId.values()].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es')))
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'No se pudo cargar la lista de equipos.'))
  }, [])

  // 2) El reporte del equipo elegido.
  const cargar = useCallback((id: number) => {
    const esta = ++peticion.current
    return obtenerReporte(`/equipo/${id}`)
      .then(r => { if (esta === peticion.current) { setReporte(r); setError('') } })
      .catch((e: unknown) => {
        if (esta === peticion.current) { setReporte(null); setError(e instanceof Error ? e.message : 'No se pudo generar el reporte.') }
      })
      .finally(() => { if (esta === peticion.current) setLoading(false) })
  }, [])

  function elegir(valor: string) {
    setError('')
    if (valor === '') { peticion.current++; setElegido(null); setReporte(null); setLoading(false); return }
    const id = Number(valor)
    setElegido(id)
    setReporte(null) // no dejar a la vista el equipo anterior mientras llega el nuevo
    setLoading(true)
    void cargar(id)
  }

  return (
    <div className="rep-contenido" aria-busy={loading}>
      <div className="rep-filtros">
        <label>
          Equipo
          <select className="rep-select" value={elegido ?? ''} onChange={e => elegir(e.target.value)}>
            <option value="">Elige un equipo…</option>
            {equipos.map(o => (
              <option key={o.id} value={o.id}>
                {o.nombre}{o.estado_disponibilidad === 'DADO_DE_BAJA' ? ' (dado de baja)' : ''}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="rep-boton"
          disabled={loading || elegido === null}
          onClick={() => { if (elegido !== null) { setLoading(true); void cargar(elegido) } }}
        >
          {loading ? 'Actualizando…' : 'Actualizar'}
        </button>
      </div>

      {error && <p className="alert alert-error" role="alert">{error}</p>}
      {elegido === null && !error && <p className="rep-vacio">Elige un equipo para ver su historial.</p>}
      {loading && !reporte && elegido !== null && <p className="rep-vacio" role="status">Generando reporte…</p>}
      {reporte && <ReporteVista reporte={reporte} />}
    </div>
  )
}
