import type { Reporte } from '../../api/reportes'
import TablaReporte from './TablaReporte'
import './reportes.css'

// Dibuja CUALQUIER reporte: título, datos clave arriba y sus tablas.
export default function ReporteVista({ reporte }: { reporte: Reporte }) {
  return (
    <div className="rep-vista">
      <h2>{reporte.titulo}</h2>
      {reporte.resumen.length > 0 && (
        <div className="rep-resumen">
          {reporte.resumen.map(d => (
            <article className="rep-dato" key={d.etiqueta}>
              <span>{d.etiqueta}</span>
              <strong>{d.valor}</strong>
            </article>
          ))}
        </div>
      )}
      {reporte.tablas.map(t => <TablaReporte key={t.titulo} tabla={t} />)}
    </div>
  )
}
