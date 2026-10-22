import type { SessionUser } from '../../api/auth'
import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { listarObjetos } from '../../api/objetos'
import type { Objeto } from '../../api/objetos'
import { listarUsuarios } from '../../api/usuarios'
import type { Usuario } from '../../api/usuarios'
import { cambiarEstadoReserva, crearReserva, listarReservas, procesarVencidas } from '../../api/reservas'
import type { AccionReserva, EstadoReserva, Reserva } from '../../api/reservas'
import './reservas.css'

const message = (e: unknown) => e instanceof Error ? e.message : 'No se pudo completar la operación.'
const formatDate = (date: string) => date.split('-').reverse().join('/')
const today = () => new Date().toLocaleDateString('sv-SE')
const labels: Record<EstadoReserva, string> = { PENDIENTE: 'Pendiente', CONFIRMADA: 'Confirmada', CANCELADA: 'Cancelada', FINALIZADA: 'Finalizada', VENCIDA: 'Vencida' }
const canReserve = (o: Objeto) => o.estado_disponibilidad === 'DISPONIBLE' && o.estado_fisico !== 'DANHADO'

export default function ReservasPage({ user, objetoInicial, onEntregar }: { user: SessionUser; objetoInicial?: number; onEntregar: (id: number) => void }) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [objetos, setObjetos] = useState<Objeto[]>([])
  const [reservas, setReservas] = useState<Reserva[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [usuarioId, setUsuarioId] = useState(user.administrador ? '' : String(user.id))
  const [objetoId, setObjetoId] = useState(objetoInicial ? String(objetoInicial) : '')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [busy, setBusy] = useState(false)
  const [filter, setFilter] = useState('')
  const [cancelTarget, setCancelTarget] = useState<Reserva | null>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const load = useCallback(() => {
    return Promise.all([user.administrador ? listarUsuarios() : Promise.resolve([]), listarObjetos(), listarReservas()])
      .then(([u, o, r]) => { setUsuarios(u); setObjetos(o); setReservas(r) })
      .catch((e: unknown) => { setLoadError(e instanceof Error ? e.message : 'No se pudieron cargar las reservas.') })
      .finally(() => setLoading(false))
  }, [user.administrador])
  async function refresh() { setLoading(true); setLoadError(''); await load() }
  useEffect(() => { void load() }, [load])
  useEffect(() => { if (cancelTarget) dialog.current?.showModal(); else dialog.current?.close() }, [cancelTarget])
  async function submit(e: FormEvent) {
    e.preventDefault(); if (busy) return
    setError(''); setNotice('')
    if (!objetoId || !usuarioId || !desde || !hasta) { setError('Completa el usuario, equipo y las fechas.'); return }
    if (desde < today() || hasta < desde) { setError('Elige fechas desde hoy y una fecha final igual o posterior al inicio.'); return }
    setBusy(true)
    try {
      const r = await crearReserva({ usuario_id: user.administrador ? Number(usuarioId) : user.id, objeto_id: Number(objetoId), fecha_inicio: desde, fecha_fin: hasta })
      setDesde(''); setHasta(''); setNotice(`Reserva #${r.id} creada. Está pendiente de confirmación.`)
      await refresh()
    } catch (e) { setError(message(e)) }
    finally { setBusy(false) }
  }
  async function act(r: Reserva, action: AccionReserva) {
    if (busy) return
    setBusy(true); setError(''); setNotice('')
    try {
      await cambiarEstadoReserva(r.id, action)
      setCancelTarget(null)
      setNotice(`Reserva #${r.id} ${action === 'confirmar' ? 'confirmada' : action === 'cancelar' ? 'cancelada' : 'finalizada'} correctamente.`)
      await refresh()
    } catch (e) { setCancelTarget(null); setError(message(e)) }
    finally { setBusy(false) }
  }
  async function expire() {
    if (busy) return
    setBusy(true); setError(''); setNotice('')
    try { const r = await procesarVencidas(); setNotice(r.length ? `${r.length} reservas marcadas como vencidas.` : 'No hay reservas pendientes de vencer.'); await refresh() }
    catch (e) { setError(message(e)) }
    finally { setBusy(false) }
  }
  const nombreUsuario = (id: number) => id === user.id ? user.nombre : usuarios.find(u => u.id === id)?.nombre ?? `Usuario #${id}`
  const nombreObjeto = (id: number) => objetos.find(o => o.id === id)?.nombre ?? `Equipo #${id} (fuera del catálogo)`
  const reservables = objetos.filter(canReserve)
  const selected = objetos.find(o => String(o.id) === objetoId)
  const rows = reservas.filter(r => !filter || r.estado === filter).sort((a, b) => b.id - a.id)
  return <div className="page-reservas">
    <header className="topbar"><div><span className="section-eyebrow">ORGANIZA TU PRÓXIMO PROYECTO</span><h1>{user.administrador ? 'Reservas de la comunidad' : 'Mis reservas'}</h1><p>{user.administrador ? 'Revisa solicitudes y confirma los recursos para cada proyecto.' : 'Elige tus fechas y sigue el estado de tus solicitudes.'}</p></div><button className="refresh-button" disabled={loading || busy} onClick={() => void refresh()}>{loading ? 'Actualizando…' : 'Actualizar'}</button></header>
    {error && <div className="alert alert-error" role="alert">{error}</div>}{notice && <div className="alert alert-ok" role="status">{notice}</div>}
    {loadError && <div className="alert alert-error" role="alert">{loadError} <button onClick={() => void refresh()}>Reintentar carga</button></div>}
    <div className="reservation-metrics">{(['PENDIENTE', 'CONFIRMADA', 'CANCELADA'] as EstadoReserva[]).map(s => <button key={s} aria-pressed={filter === s} onClick={() => setFilter(filter === s ? '' : s)}><span className={`reservation-dot estado-${s.toLowerCase()}`} /><span>{s === 'PENDIENTE' ? 'Por confirmar' : s === 'CONFIRMADA' ? 'Confirmadas' : 'Canceladas'}</span><b>{loading || loadError ? '—' : reservas.filter(r => r.estado === s).length}</b></button>)}</div>
    <section className="panel reservation-create"><div className="panel-header"><div><span className="section-eyebrow">01 · ELIGE TU EQUIPO Y FECHAS</span><h2>Nueva reserva</h2><p>Las fechas inicial y final están incluidas. Una reserva futura no bloquea otros períodos.</p></div><span className="reservation-step" aria-hidden="true">↗</span></div>
      {loading ? <p className="hint" role="status">Consultando disponibilidad…</p> : loadError ? <p className="hint">Recarga los datos para crear una reserva.</p> : !reservables.length ? <p className="hint">No hay equipos disponibles para reservar en este momento.</p> : <form onSubmit={submit}><fieldset className="reservation-form" disabled={busy}>
        {user.administrador ? <label className="field">Usuario<select required value={usuarioId} onChange={e => setUsuarioId(e.target.value)}><option value="">Selecciona un usuario</option>{usuarios.filter(u => u.estado === 'ACTIVO').map(u => <option key={u.id} value={u.id}>{u.nombre}</option>)}</select></label> : <div className="reservation-owner"><span>Reserva para</span><strong>{user.nombre}</strong></div>}
        <label className="field">Equipo<select required value={objetoId} onChange={e => setObjetoId(e.target.value)}><option value="">Selecciona un equipo</option>{selected && !canReserve(selected) && <option value={selected.id} disabled>{selected.nombre} · No disponible</option>}{reservables.map(o => <option value={o.id} key={o.id}>{o.nombre}</option>)}</select></label>
        <label className="field">Desde<input type="date" required min={today()} value={desde} onChange={e => { setDesde(e.target.value); if (hasta && hasta < e.target.value) setHasta('') }} /></label>
        <label className="field">Hasta<input type="date" required min={desde || today()} value={hasta} onChange={e => setHasta(e.target.value)} /></label>
        <button className="btn" disabled={Boolean(selected && !canReserve(selected))}>{busy ? 'Guardando…' : 'Crear reserva'}</button>
      </fieldset><p className="reservation-help">La solicitud queda pendiente hasta que el administrador la confirme. No se permiten fechas que coincidan con otra reserva activa del mismo equipo.</p></form>}
    </section>
    <section className="panel reservation-list"><div className="panel-header"><div><span className="section-eyebrow">02 · SIGUE TUS SOLICITUDES</span><h2>{user.administrador ? 'Registro de reservas' : 'Historial de reservas'}</h2><p role="status">{loading ? 'Cargando…' : `${rows.length} ${rows.length === 1 ? 'reserva' : 'reservas'}`}</p></div><div className="reservation-list-tools"><label><span className="sr-only">Filtrar reservas por estado</span><select value={filter} onChange={e => setFilter(e.target.value)}><option value="">Todos los estados</option>{Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>{user.administrador && <button className="text-button" disabled={busy || loading} onClick={() => void expire()}>Procesar vencidas</button>}</div></div>
      {loading ? <p className="hint">Cargando reservas…</p> : loadError ? <p className="hint">No se pudieron actualizar las reservas.</p> : !rows.length ? <div className="reservation-empty"><strong>{filter ? 'No hay reservas con ese estado' : 'Tu próximo proyecto empieza con una reserva'}</strong><p>{filter ? 'Selecciona otro estado para consultar el historial.' : 'Elige un equipo y tus fechas en el formulario de arriba.'}</p>{filter && <button className="text-button" onClick={() => setFilter('')}>Ver todas las reservas</button>}</div> : <div className="reservation-table-wrap"><table className="reservation-table"><thead><tr><th>Reserva / Usuario</th><th>Equipo</th><th>Período</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows.map(r => <tr key={r.id} data-reserva-id={r.id}><td><small>RESERVA #{r.id}</small><strong>{nombreUsuario(r.usuario_id)}</strong></td><td>{nombreObjeto(r.objeto_id)}</td><td><span>{formatDate(r.fecha_inicio)}</span><small>hasta {formatDate(r.fecha_fin)}</small></td><td><span className={`status estado-${r.estado.toLowerCase()}`}>{labels[r.estado]}</span></td><td><div className="reservas-acciones">{user.administrador && r.estado === 'PENDIENTE' && <button className="btn btn-small" disabled={busy} onClick={() => void act(r, 'confirmar')}>Confirmar</button>}{user.administrador && r.estado === 'CONFIRMADA' && <button className="btn btn-small btn-ghost" disabled={busy} onClick={() => onEntregar(r.id)}>Entregar equipo</button>}{(r.estado === 'PENDIENTE' || r.estado === 'CONFIRMADA') ? <button className="btn btn-small btn-danger" disabled={busy} onClick={() => setCancelTarget(r)}>Cancelar</button> : <span className="reservation-closed">Sin acciones pendientes</span>}</div></td></tr>)}</tbody></table></div>}
    </section>
    <dialog className="reservation-confirm" ref={dialog} onCancel={e => { e.preventDefault(); if (!busy) setCancelTarget(null) }} aria-labelledby="cancel-title"><span className="section-eyebrow">CONFIRMACIÓN</span><h2 id="cancel-title">¿Cancelar la reserva?</h2><p>La reserva #{cancelTarget?.id} de {cancelTarget && nombreObjeto(cancelTarget.objeto_id)} se cancelará y sus fechas quedarán libres.</p><footer><button className="refresh-button" disabled={busy} onClick={() => setCancelTarget(null)}>Conservar reserva</button><button className="btn btn-danger" disabled={busy} onClick={() => cancelTarget && void act(cancelTarget, 'cancelar')}>{busy ? 'Cancelando…' : 'Sí, cancelar reserva'}</button></footer></dialog>
  </div>
}
