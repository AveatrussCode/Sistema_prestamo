import DevolucionForm from './DevolucionForm'
import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { SessionUser } from '../../api/auth'
import { listarPrestamos, entregarEquipo } from '../../api/prestamos'
import type { Prestamo } from '../../api/prestamos'
import { listarReservas } from '../../api/reservas'
import type { Reserva } from '../../api/reservas'
import { listarObjetos } from '../../api/objetos'
import type { Objeto } from '../../api/objetos'
import { listarUsuarios } from '../../api/usuarios'
import type { Usuario } from '../../api/usuarios'
import './prestamo.css'

const formatDate = (value: string) => value.split('-').reverse().join('/')
const today = () => new Date().toLocaleDateString('sv-SE')
export default function PrestamosPage({ user, reservaInicial, onReservas }: { user: SessionUser; reservaInicial?: number; onReservas: () => void }) {
  const [prestamos, setPrestamos] = useState<Prestamo[]>([])
  const [returning, setReturning] = useState<Prestamo | null>(null)
  const [reservas, setReservas] = useState<Reserva[]>([])
  const [objetos, setObjetos] = useState<Objeto[]>([])
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [selectedId, setSelectedId] = useState(reservaInicial ? String(reservaInicial) : '')
  const [notes, setNotes] = useState('')
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const dialog = useRef<HTMLDialogElement>(null)
  const successNotice = useRef<HTMLParagraphElement>(null)
  useEffect(() => { if (notice) successNotice.current?.focus({ preventScroll: true }) }, [notice])
  const load = useCallback(() => {
    return Promise.all([listarPrestamos(), user.administrador ? listarReservas() : Promise.resolve([]), user.administrador ? listarObjetos() : Promise.resolve([]), user.administrador ? listarUsuarios() : Promise.resolve([])])
      .then(([p, r, o, u]) => { setPrestamos(p); setReservas(r); setObjetos(o); setUsuarios(u) })
      .catch((e: unknown) => { setError(e instanceof Error ? e.message : 'No se pudieron cargar los préstamos.') })
      .finally(() => setLoading(false))
  }, [user.administrador])
  async function refresh() { setLoading(true); setError(''); await load() }
  useEffect(() => { void load() }, [load])
  const confirmed = reservas.filter(r => r.estado === 'CONFIRMADA')
  const selected = confirmed.find(r => String(r.id) === selectedId)
  const equipo = objetos.find(o => o.id === selected?.objeto_id)
  const borrower = usuarios.find(u => u.id === selected?.usuario_id)
  const reason = !selected ? 'Selecciona una reserva confirmada para preparar la entrega.'
    : today() < selected.fecha_inicio ? `La entrega estará disponible desde el ${formatDate(selected.fecha_inicio)}.`
    : today() > selected.fecha_fin ? 'Esta reserva ya venció. No se puede entregar el equipo.'
    : !borrower || borrower.estado !== 'ACTIVO' ? 'El usuario debe estar activo para recibir el equipo.'
    : !equipo || equipo.estado_disponibilidad !== 'DISPONIBLE' || equipo.estado_fisico === 'DANHADO' ? 'El equipo no está disponible para entregar.' : ''
  function review(event: FormEvent) { event.preventDefault(); if (!reason && !busy) dialog.current?.showModal() }
  async function deliver() {
    if (!selected || reason || busy) return
    setBusy(true); setError(''); setNotice('')
    try {
      const result = await entregarEquipo(selected.id, notes.trim())
      dialog.current?.close(); setSelectedId(''); setNotes('')
      await refresh(); setNotice(`Entrega registrada: préstamo #${result.id}. ${result.equipo} figura como prestado.`)
    } catch (e) { dialog.current?.close(); setError(e instanceof Error ? e.message : 'No se pudo registrar la entrega.') }
    finally { setBusy(false) }
  }
  const rows = prestamos.filter(p => !filter || p.estado === filter)
  return <section className="prestamos-page">
    <header className="topbar"><div><span className="section-eyebrow">DEL CATÁLOGO A TU PROYECTO</span><h1>{user.administrador ? 'Préstamos y entregas' : 'Mis préstamos'}</h1><p>{user.administrador ? 'Registra la entrega física de equipos y consulta sus plazos.' : 'Consulta los equipos que recibiste y la fecha prevista de devolución.'}</p></div><button className="refresh-button" disabled={loading || busy} onClick={() => void refresh()}>{loading ? 'Actualizando…' : 'Actualizar'}</button></header>
    {error && <p className="alert alert-error" role="alert">{error} <button onClick={() => void refresh()}>Reintentar</button></p>}{notice && <p ref={successNotice} tabIndex={-1} className="inventory-success" role="status">{notice}</p>}
    <div className="prestamos-resumen">{[['En curso', prestamos.filter(p => p.estado === 'ACTIVO' || p.estado === 'VENCIDO').length], ['Fuera de plazo', prestamos.filter(p => p.estado === 'VENCIDO').length], ['Devueltos', prestamos.filter(p => p.estado === 'DEVUELTO').length], ['Total registrado', prestamos.length]].map(([name, value]) => <article className="prestamo-metrica" key={name}><span>{name}</span><strong>{loading || error ? '—' : value}</strong></article>)}</div>
    {user.administrador && <section className="panel loan-delivery"><header className="panel-header"><div><span className="section-eyebrow">01 · ENTREGA FÍSICA</span><h2>Entregar un equipo</h2><p>La reserva debe estar confirmada y dentro de sus fechas.</p></div><button className="text-button" onClick={onReservas}>Ver reservas →</button></header>{loading ? <p className="hint">Consultando reservas confirmadas…</p> : error ? <p className="hint">Actualiza los datos para preparar una entrega.</p> : !confirmed.length ? <div className="loan-empty"><strong>No hay reservas confirmadas para entregar</strong><p>Confirma una solicitud en Reservas para continuar.</p><button className="text-button" onClick={onReservas}>Gestionar reservas →</button></div> : <form onSubmit={review}><fieldset disabled={busy}><label>Reserva confirmada<select aria-label="Reserva confirmada" required value={selectedId} onChange={e => { setSelectedId(e.target.value); setNotes('') }}><option value="">Selecciona una reserva</option>{confirmed.map(r => <option key={r.id} value={r.id}>#{r.id} · {objetos.find(o => o.id === r.objeto_id)?.nombre ?? `Equipo #${r.objeto_id}`} · {usuarios.find(u => u.id === r.usuario_id)?.nombre ?? `Usuario #${r.usuario_id}`}</option>)}</select></label>
      {selected && <div className="loan-review"><div><small>RECIBE</small><strong>{borrower?.nombre ?? 'Usuario no disponible'}</strong></div><div><small>EQUIPO</small><strong>{equipo?.nombre ?? 'Fuera del catálogo'}</strong></div><div><small>DEVOLUCIÓN PREVISTA</small><strong>{formatDate(selected.fecha_fin)}</strong></div></div>}
      <label>Observaciones de entrega<textarea maxLength={2000} rows={3} placeholder="Accesorios incluidos y estado del equipo al entregar" value={notes} onChange={e => setNotes(e.target.value)} /></label>{reason && <p className="loan-help">{reason}</p>}<button className="primary-button" disabled={Boolean(reason)}>{busy ? 'Registrando…' : 'Revisar entrega'}</button></fieldset></form>}</section>}
    <section className="panel loan-list"><header className="panel-header"><div><span className="section-eyebrow">{user.administrador ? '02 ·' : ''} SEGUIMIENTO</span><h2>Registro de préstamos</h2><p>{loading ? 'Cargando…' : `${rows.length} registros`}</p></div><label><span className="sr-only">Filtrar préstamos</span><select aria-label="Filtrar préstamos" value={filter} onChange={e => setFilter(e.target.value)}><option value="">Todos los estados</option><option value="ACTIVO">Activos</option><option value="VENCIDO">Vencidos</option><option value="DEVUELTO">Devueltos</option><option value="CANCELADO">Cancelados</option></select></label></header>{loading ? <p className="hint">Cargando préstamos…</p> : error ? <p className="hint">No se pudo actualizar el registro.</p> : !rows.length ? <div className="loan-empty"><strong>{filter ? 'No hay préstamos con ese estado' : 'Todavía no hay préstamos registrados'}</strong><p>{filter ? 'Prueba con otro estado.' : 'Los equipos aparecerán aquí cuando se registre su entrega.'}</p>{filter && <button className="text-button" onClick={() => setFilter('')}>Ver todos</button>}</div> : <div className="prestamos-tabla"><table className="loan-table"><thead><tr><th>Préstamo / Usuario</th><th>Equipo</th><th>Entrega</th><th>Devolución prevista</th><th>Estado</th>{user.administrador && <th>Acciones</th>}</tr></thead><tbody>{rows.map(p => <tr key={p.id} data-prestamo-id={p.id}><td><small>PRÉSTAMO #{p.id} · RESERVA #{p.reserva_id}</small><strong>{p.usuario}</strong></td><td><strong>{p.equipo}</strong>{p.observaciones_entrega && <small className="loan-notes">{p.observaciones_entrega}</small>}{p.devolucion && <details className="return-details"><summary>Ver devolución</summary><p>Recibido el {formatDate(p.devolucion.fecha)} · {p.devolucion.estado_fisico === 'DANHADO' ? 'Dañado' : p.devolucion.estado_fisico === 'REGULAR' ? 'Regular' : 'Bueno'}</p>{p.devolucion.fuera_de_plazo && <p>Devuelto fuera de plazo.</p>}{p.devolucion.observaciones && <p>{p.devolucion.observaciones}</p>}</details>}</td><td>{formatDate(p.fecha_inicio)}</td><td>{formatDate(p.fecha_devolucion_prevista)}</td><td><span className={`prestamo-estado estado-${p.estado.toLowerCase()}`}>{p.estado === 'ACTIVO' ? 'Activo' : p.estado === 'VENCIDO' ? 'Vencido' : p.estado === 'DEVUELTO' ? 'Devuelto' : 'Cancelado'}</span></td>{user.administrador && <td>{p.estado === 'ACTIVO' || p.estado === 'VENCIDO' ? <button className="refresh-button" disabled={busy || loading} onClick={() => { setReturning(p); setNotice('') }}>Registrar devolución</button> : <span className="loan-closed">Cerrado</span>}</td>}</tr>)}</tbody></table></div>}</section>
    <dialog ref={dialog} className="loan-confirm" onCancel={e => { if (busy) e.preventDefault() }} aria-labelledby="delivery-title"><span className="section-eyebrow">CONFIRMA LA ENTREGA FÍSICA</span><h2 id="delivery-title">¿El usuario recibió el equipo?</h2><p>Registrarás la entrega de <strong>{equipo?.nombre}</strong> a <strong>{borrower?.nombre}</strong>.</p><p>Devolución prevista: <strong>{selected && formatDate(selected.fecha_fin)}</strong>. El equipo pasará a “Prestado” y la reserva quedará finalizada.</p><footer><button className="refresh-button" disabled={busy} onClick={() => dialog.current?.close()}>Volver</button><button className="primary-button" disabled={busy} onClick={() => void deliver()}>{busy ? 'Registrando…' : 'Confirmar entrega'}</button></footer></dialog>
    {user.administrador && returning && <DevolucionForm prestamo={returning} onClose={() => setReturning(null)} onSaved={p => { setReturning(null); setPrestamos(current => current.map(item => item.id === p.id ? p : item)); void refresh(); setNotice(`Devolución registrada: préstamo #${p.id}. ${p.devolucion?.estado_fisico === 'DANHADO' ? 'El equipo quedó no disponible para revisión.' : 'El equipo está disponible nuevamente.'}`) }} />}
  </section>
}
