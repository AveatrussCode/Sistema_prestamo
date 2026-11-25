import { useEffect, useState } from 'react'
import { miCredibilidad } from '../api/credibilidad'
import type { MiCredibilidad } from '../api/credibilidad'

export default function CredibilidadPanel() {
  const [c, setC] = useState<MiCredibilidad | null>(null)
  useEffect(() => { miCredibilidad().then(setC).catch(() => setC(null)) }, [])
  if (!c) return null
  const l = c.limites
  return (
    <section className="credibilidad-panel">
      <h3>Tu nivel: {c.nivel_etiqueta}</h3>
      <meter min={0} max={c.tope} value={c.valor} /> <span>{c.valor}/{c.tope}</span>
      <p>{l.puede_reservar
        ? `Puedes reservar hasta ${l.max_dias} día(s), con ${l.max_equipos} equipo(s) a la vez.`
        : 'Por ahora no puedes reservar. Habla con un administrador.'}</p>
      <h4>Últimos movimientos</h4>
      <ul>
        {c.movimientos.slice(0, 5).map(m => (
          <li key={m.id}>{m.puntos > 0 ? '+' : ''}{Number(m.puntos.toFixed(1))} · {m.motivo}{m.estado === 'aplicado' ? '' : ' (anulado)'}</li>
        ))}
      </ul>
    </section>
  )
}