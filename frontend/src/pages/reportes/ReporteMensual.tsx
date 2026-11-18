import { useCallback, useEffect, useRef, useState } from 'react'
import { obtenerReporte } from '../../api/reportes'
import type { Reporte } from '../../api/reportes'
import ReporteVista from './ReporteVista'
import './reportes.css'

// Reporte por periodo: cómo estuvo el sistema en un MES completo o en un RANGO de fechas.
// Un mes es solo un atajo: el backend siempre recibe "desde" y "hasta" (GET /reportes/periodo).

type Modo = 'mes' | 'rango'

const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
const dos = (n: number) => String(n).padStart(2, '0')
const iso = (f: Date) => `${f.getFullYear()}-${dos(f.getMonth() + 1)}-${dos(f.getDate())}` // fecha local, sin desfase de zona horaria

function rangoDelMes(anio: number, mes: number) { // mes: 1 a 12
  return { desde: `${anio}-${dos(mes)}-01`, hasta: iso(new Date(anio, mes, 0)) } // día 0 del mes siguiente = último día de este
}

export default function ReporteMensual() {
  const hoy = new Date()
  const [modo, setModo] = useState<Modo>('mes')
  const [anio, setAnio] = useState(hoy.getFullYear())
  const [mes, setMes] = useState(hoy.getMonth() + 1)
  const [desde, setDesde] = useState(() => rangoDelMes(hoy.getFullYear(), hoy.getMonth() + 1).desde)
  const [hasta, setHasta] = useState(() => iso(hoy))
  const [reporte, setReporte] = useState<Reporte | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const peticion = useRef(0) // solo vale la respuesta de la última petición

  const cargar = useCallback((d: string, h: string) => {
    const esta = ++peticion.current
    return obtenerReporte(`/periodo?desde=${d}&hasta=${h}`)
      .then(r => { if (esta === peticion.current) { setReporte(r); setError('') } })
      .catch((e: unknown) => {
        if (esta === peticion.current) { setReporte(null); setError(e instanceof Error ? e.message : 'No se pudo generar el reporte.') }
      })
      .finally(() => { if (esta === peticion.current) setLoading(false) })
  }, [])

  // Al abrir la pantalla se muestra el mes actual (del día 1 a hoy).
  const [inicial] = useState(() => ({ desde: rangoDelMes(hoy.getFullYear(), hoy.getMonth() + 1).desde, hasta: iso(hoy) }))
  useEffect(() => { void cargar(inicial.desde, inicial.hasta) }, [cargar, inicial])

  function generar() {
    const rango = modo === 'mes' ? rangoDelMes(anio, mes) : { desde, hasta }
    if (!rango.desde || !rango.hasta) { setError('Indica la fecha inicial y la final.'); return }
    if (rango.hasta < rango.desde) { setError('La fecha final no puede ser anterior a la inicial.'); return }
    setError('')
    setLoading(true)
    void cargar(rango.desde, rango.hasta)
  }

  const anioValido = Number.isInteger(anio) && anio >= 2000 && anio <= 2100

  return (
    <div className="rep-contenido" aria-busy={loading}>
      <div className="rep-filtros">
        <div className="rep-modos" role="group" aria-label="Tipo de periodo">
          <button type="button" className={modo === 'mes' ? 'selected' : ''} aria-pressed={modo === 'mes'} onClick={() => setModo('mes')}>Por mes</button>
          <button type="button" className={modo === 'rango' ? 'selected' : ''} aria-pressed={modo === 'rango'} onClick={() => setModo('rango')}>Rango de fechas</button>
        </div>

        {modo === 'mes' ? (
          <>
            <label>
              Mes
              <select className="rep-select" value={mes} onChange={e => setMes(Number(e.target.value))}>
                {MESES.map((nombre, i) => <option key={nombre} value={i + 1}>{nombre}</option>)}
              </select>
            </label>
            <label>
              Año
              <input
                className="rep-select rep-anio"
                type="number"
                min={2000}
                max={2100}
                value={anio}
                onChange={e => setAnio(Number(e.target.value))}
              />
            </label>
          </>
        ) : (
          <>
            <label>
              Desde
              <input className="rep-select" type="date" value={desde} max={hasta || undefined} onChange={e => setDesde(e.target.value)} />
            </label>
            <label>
              Hasta
              <input className="rep-select" type="date" value={hasta} min={desde || undefined} onChange={e => setHasta(e.target.value)} />
            </label>
          </>
        )}

        <button type="button" className="rep-boton" disabled={loading || (modo === 'mes' && !anioValido)} onClick={generar}>
          {loading ? 'Generando…' : 'Generar reporte'}
        </button>
      </div>

      {error && <p className="alert alert-error" role="alert">{error}</p>}
      {loading && !reporte && <p className="rep-vacio" role="status">Generando reporte…</p>}
      {reporte && <ReporteVista reporte={reporte} />}
    </div>
  )
}
