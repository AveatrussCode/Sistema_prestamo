import { useMemo, useState } from 'react'
import type { Fila, TablaDatos, Valor } from '../../api/reportes'
import './reportes.css'

const FECHA_ISO = /^\d{4}-\d{2}-\d{2}$/

// Cómo se ve cada valor en pantalla (y en el CSV).
function texto(valor: Valor | undefined): string {
  if (valor === null || valor === undefined || valor === '') return '—'
  if (typeof valor === 'boolean') return valor ? 'Sí' : 'No'
  if (typeof valor === 'string' && FECHA_ISO.test(valor)) return valor.split('-').reverse().join('/')
  return String(valor)
}

function comparar(a: Valor | undefined, b: Valor | undefined): number {
  if (typeof a === 'number' && typeof b === 'number') return a - b
  return String(a ?? '').localeCompare(String(b ?? ''), 'es', { numeric: true })
}

function descargarCsv(tabla: TablaDatos, filas: Fila[]) {
  const celda = (v: string) => `"${v.replace(/"/g, '""')}"`
  const lineas = [tabla.columnas.map(c => celda(c.titulo)).join(',')]
  for (const fila of filas) lineas.push(tabla.columnas.map(c => celda(texto(fila[c.clave]))).join(','))
  // \ufeff = marca para que Excel muestre bien las tildes
  const blob = new Blob(['\ufeff' + lineas.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = `${tabla.titulo.toLowerCase().replace(/\s+/g, '-')}.csv`
  enlace.click()
  URL.revokeObjectURL(url)
}

// Tabla reutilizable: sirve para cualquier reporte (ordenar, buscar, exportar).
export default function TablaReporte({ tabla }: { tabla: TablaDatos }) {
  const [busqueda, setBusqueda] = useState('')
  const [orden, setOrden] = useState<{ clave: string; asc: boolean } | null>(null)

  const filas = useMemo(() => {
    const q = busqueda.trim().toLowerCase()
    const visibles = q
      ? tabla.filas.filter(f => tabla.columnas.some(c => texto(f[c.clave]).toLowerCase().includes(q)))
      : [...tabla.filas]
    if (orden) {
      const { clave, asc } = orden
      visibles.sort((x, y) => (asc ? 1 : -1) * comparar(x[clave], y[clave]))
    }
    return visibles
  }, [tabla, busqueda, orden])

  function ordenarPor(clave: string) {
    setOrden(actual => (actual?.clave === clave ? { clave, asc: !actual.asc } : { clave, asc: true }))
  }

  return (
    <section className="rep-tabla-bloque">
      <div className="rep-tabla-barra">
        <h3>{tabla.titulo} <small>({filas.length})</small></h3>
        <input
          type="search"
          placeholder="Buscar en la tabla"
          aria-label={`Buscar en ${tabla.titulo}`}
          value={busqueda}
          onChange={e => setBusqueda(e.target.value)}
        />
        <button type="button" className="rep-boton" disabled={!filas.length} onClick={() => descargarCsv(tabla, filas)}>
          Exportar CSV
        </button>
      </div>

      {filas.length === 0 ? (
        <p className="rep-vacio">No hay datos para mostrar.</p>
      ) : (
        <div className="rep-tabla-scroll">
          <table className="rep-tabla">
            <thead>
              <tr>
                {tabla.columnas.map(c => (
                  <th key={c.clave} aria-sort={orden?.clave === c.clave ? (orden.asc ? 'ascending' : 'descending') : 'none'}>
                    <button type="button" onClick={() => ordenarPor(c.clave)}>
                      {c.titulo}
                      <span aria-hidden="true">{orden?.clave === c.clave ? (orden.asc ? ' ▲' : ' ▼') : ''}</span>
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filas.map((f, i) => (
                <tr key={i}>
                  {tabla.columnas.map(c => <td key={c.clave}>{texto(f[c.clave])}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
