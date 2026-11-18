import { useCallback, useEffect, useState } from 'react'
import { obtenerReporte } from '../../api/reportes'
import type { Reporte } from '../../api/reportes'
import { listarUsuarios } from '../../api/usuarios'
import type { Usuario } from '../../api/usuarios'
import ReporteVista from './ReporteVista'
import './reportes.css'

// Reporte de usuario (Persona 2): préstamos y reservas de una persona.
// - El administrador elige a la persona en una lista.
// - Si se le pasa `usuarioId` (alguien viendo SU propio reporte), no se muestra la lista.
export default function ReporteUsuario({ usuarioId }: { usuarioId?: number }) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [elegido, setElegido] = useState<number | null>(usuarioId ?? null)
  const [reporte, setReporte] = useState<Reporte | null>(null)
  const [loading, setLoading] = useState(usuarioId !== undefined)
  const [error, setError] = useState('')

  // 1) El administrador necesita la lista de personas para poder elegir.
  useEffect(() => {
    if (usuarioId !== undefined) return
    listarUsuarios()
      .then(setUsuarios)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'No se pudo cargar la lista de usuarios.'))
  }, [usuarioId])

  // 2) Cada vez que cambia la persona elegida, se pide su reporte al backend.
  const cargar = useCallback(() => {
    if (elegido === null) return Promise.resolve()
    return obtenerReporte(`/usuario/${elegido}`)
      .then(r => { setReporte(r); setError('') })
      .catch((e: unknown) => { setReporte(null); setError(e instanceof Error ? e.message : 'No se pudo generar el reporte.') })
      .finally(() => setLoading(false))
  }, [elegido])

  useEffect(() => { void cargar() }, [cargar])

  function elegir(valor: string) {
    setError('')
    if (valor === '') { setElegido(null); setReporte(null); setLoading(false); return }
    setLoading(true)
    setElegido(Number(valor))
  }

  return (
    <div className="rep-contenido" aria-busy={loading}>
      <div className="rep-filtros">
        {usuarioId === undefined && (
          <label>
            Persona
            <select
              value={elegido ?? ''}
              onChange={e => elegir(e.target.value)}
              style={{ padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 8, background: '#fff', minWidth: 280 }}
            >
              <option value="">Elige a una persona…</option>
              {usuarios.map(u => <option key={u.id} value={u.id}>{u.nombre} · {u.correo}</option>)}
            </select>
          </label>
        )}
        <button
          type="button"
          className="rep-boton"
          disabled={loading || elegido === null}
          onClick={() => { setLoading(true); void cargar() }}
        >
          {loading ? 'Actualizando…' : 'Actualizar'}
        </button>
      </div>

      {error && <p className="alert alert-error" role="alert">{error}</p>}
      {elegido === null && !error && <p className="rep-vacio">Elige a una persona para ver su reporte.</p>}
      {loading && !reporte && elegido !== null && <p className="rep-vacio" role="status">Generando reporte…</p>}
      {reporte && <ReporteVista reporte={reporte} />}
    </div>
  )
}
