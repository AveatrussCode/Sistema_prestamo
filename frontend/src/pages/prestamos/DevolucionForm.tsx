import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { devolverEquipo } from '../../api/prestamos'
import type { Prestamo } from '../../api/prestamos'

export default function DevolucionForm({ prestamo, onClose, onSaved }: { prestamo: Prestamo; onClose: () => void; onSaved: (p: Prestamo) => void }) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [estado, setEstado] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { const element = dialog.current; element?.showModal(); return () => element?.close() }, [])
  async function save(e: FormEvent) {
    e.preventDefault(); if (busy) return
    setError(''); setBusy(true)
    try { onSaved(await devolverEquipo(prestamo.id, estado, observaciones.trim())) }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo registrar la devolución.') }
    finally { setBusy(false) }
  }
  return <dialog ref={dialog} className="loan-confirm return-dialog" aria-labelledby="return-title" onCancel={e => { e.preventDefault(); if (!busy) onClose() }}>
    <span className="section-eyebrow">RECEPCIÓN FÍSICA · PRÉSTAMO #{prestamo.id}</span><h2 id="return-title">Registrar devolución</h2><p>Recibes <strong>{prestamo.equipo}</strong> de <strong>{prestamo.usuario}</strong>. La devolución se registrará con la fecha de hoy.</p>
    {prestamo.estado === 'VENCIDO' && <p className="return-warning">El préstamo está fuera de plazo. El historial conservará la fecha real de devolución.</p>}
    {error && <p className="alert alert-error" role="alert">{error}</p>}
    <form onSubmit={save}><fieldset disabled={busy}><label>Estado físico al recibir<select autoFocus aria-label="Estado físico al recibir" required value={estado} onChange={e => setEstado(e.target.value)}><option value="" disabled>Selecciona el estado del equipo</option><option value="BUENO">Bueno</option><option value="REGULAR">Regular</option><option value="DANHADO">Dañado</option></select></label><label>Observaciones de devolución<textarea required={estado === 'DANHADO'} maxLength={2000} rows={3} placeholder="Accesorios recibidos y observaciones sobre el estado" value={observaciones} onChange={e => setObservaciones(e.target.value)} /></label>
      <p className={`return-outcome ${estado === 'DANHADO' ? 'return-warning' : ''}`}>{!estado ? 'Revisa el equipo y sus accesorios antes de confirmar.' : estado === 'DANHADO' ? 'Describe el daño. El préstamo se cerrará y el equipo quedará no disponible para revisión.' : 'El préstamo se cerrará y el equipo quedará disponible para nuevas reservas.'}</p>
    </fieldset><footer><button type="button" className="refresh-button" disabled={busy} onClick={onClose}>Volver</button><button className="primary-button" disabled={busy || !estado}>{busy ? 'Registrando…' : 'Confirmar devolución'}</button></footer></form>
  </dialog>
}
