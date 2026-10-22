import PrestamosPage from './pages/prestamos/PrestamoPage'
import MiPerfilPage from './usuario/MiPerfilPage'
import type { SessionUser } from './api/auth'
import { useCallback, useEffect, useState } from 'react'
import { listarUsuarios } from './api/usuarios'
import type { Usuario } from './api/usuarios'
import { listarObjetos } from './api/objetos'
import type { Objeto } from './api/objetos'
import { listarReservas } from './api/reservas'
import type { Reserva } from './api/reservas'
import ReservasPage from './pages/reservas/ReservasPage'
import CatalogoPage from './pages/catalogo/CatalogoPage'
import UsuarioPage from './usuario/UsuarioPage'
import './Workspace.css'
import './VisualRefresh.css'

type Page = 'Resumen' | 'Mi perfil' | 'Usuarios' | 'Equipos' | 'Reservas' | 'Préstamos'
const paths: Record<string, string> = {
  Resumen: 'M3 10 12 3l9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z',
  Equipos: 'M3 4h18v12H3ZM8 21h8M12 16v5',
  Reservas: 'M5 5h14v16H5ZM8 3v4M16 3v4M5 10h14M9 14h2M13 17h2',
  Usuarios: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M17 4a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-4',
  'Mi perfil': 'M20 21v-2a6 6 0 0 0-6-6h-4a6 6 0 0 0-6 6v2M12 9a4 4 0 1 0 0-8 4 4 0 0 0 0 8',
  'Préstamos': 'M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4',
  Salir: 'M9 3H3v18h6M14 7l5 5-5 5M8 12h11',
}
function Icon({ name }: { name: string }) {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name] ?? paths.Equipos} /></svg>
}

export default function Workspace({ user, logout, onUserChange, logoutBusy = false, logoutError = '' }: { logoutBusy?: boolean; logoutError?: string; user: SessionUser; logout: () => void; onUserChange: (user: SessionUser) => void }) {
  const [page, setPage] = useState<Page>('Resumen')
  const [selectedObject, setSelectedObject] = useState<number | undefined>()
  const [selectedReserva, setSelectedReserva] = useState<number | undefined>()
  const [users, setUsers] = useState<Usuario[]>([])
  const [objects, setObjects] = useState<Objeto[]>([])
  const [reservations, setReservations] = useState<Reserva[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const dateLabel = new Intl.DateTimeFormat('es-PE', { weekday: 'short', day: 'numeric', month: 'short' }).format(new Date())
  const role = user.administrador ? 'Administrativo' : user.tipo === 'profesor' ? 'Profesor' : 'Estudiante'
  const label = (p: Page) => p === 'Préstamos' && !user.administrador ? 'Mis préstamos' : p === 'Resumen' ? 'Inicio' : p === 'Equipos' ? 'Catálogo' : p === 'Reservas' && !user.administrador ? 'Mis reservas' : p
  const load = useCallback(() => {
    return Promise.all([user.administrador ? listarUsuarios() : Promise.resolve([]), listarObjetos(), listarReservas()])
      .then(([u, o, r]) => { setUsers(u); setObjects(o); setReservations(r) })
      .catch((e: unknown) => { setError(e instanceof Error ? e.message : 'No se pudieron cargar los datos.') })
      .finally(() => setLoading(false))
  }, [user.administrador])
  async function refresh() { setLoading(true); setError(''); await load() }
  useEffect(() => { void load() }, [load])
  function navigate(next: Page) { if (next !== 'Préstamos') setSelectedReserva(undefined); if (next !== 'Reservas') setSelectedObject(undefined); setPage(next); if (next === 'Resumen') void refresh() }
  const available = objects.filter(o => o.estado_disponibilidad === 'DISPONIBLE')
  const pending = reservations.filter(r => r.estado === 'PENDIENTE').length
  const metrics = [
    { title: 'Equipos disponibles', count: available.length, detail: 'Listos para tus proyectos', icon: 'Equipos' },
    { title: user.administrador ? 'Reservas registradas' : 'Mis reservas', count: reservations.length, detail: 'Consulta y administra tus solicitudes', icon: 'Reservas' },
    { title: 'Por confirmar', count: pending, detail: 'Reservas pendientes de aprobación', icon: 'Préstamos' },
    { title: user.administrador ? 'Usuarios registrados' : 'Equipos en catálogo', count: user.administrador ? users.length : objects.length, detail: user.administrador ? 'Nuestra comunidad EPCC' : 'Recursos de la escuela', icon: user.administrador ? 'Usuarios' : 'Equipos' },
  ]
  return <div className={`workspace portal-${user.administrador ? 'admin' : user.tipo}`}>
    <a className="skip-content" href="#workspace-main">Ir al contenido</a>
    <aside className="workspace-nav">
      <div className="workspace-brand"><img src="/epcc.jpg" alt="EPCC UNSA" /><div><strong>EPCC<span>Recursos & préstamos</span></strong></div></div>
      <span className="nav-caption">ESPACIO DE TRABAJO</span>
      <nav aria-label="Navegación principal">{(['Resumen', 'Equipos', 'Reservas', 'Préstamos', 'Usuarios', 'Mi perfil'] as Page[]).filter(p => user.administrador || p !== 'Usuarios').map(p => <button key={p} aria-label={label(p)} aria-current={page === p ? 'page' : undefined} className={page === p ? 'selected' : ''} onClick={() => navigate(p)}><Icon name={p} /><span>{label(p)}</span>{p === 'Reservas' && pending > 0 && <b className="nav-count">{pending}</b>}</button>)}</nav>
      <div className="nav-note"><span className="live-dot" />Tu espacio para crear<p>Encuentra los recursos para tu próxima idea.</p></div>
      <div className="nav-account"><span className="account-avatar">{user.nombre[0]}</span><div><strong>{user.nombre}</strong><small>{role}</small></div></div>
      <button className="logout-button" disabled={logoutBusy} onClick={logout}><Icon name="Salir" /><span>{logoutBusy ? 'Cerrando…' : 'Cerrar sesión'}</span></button>
    </aside>
    <main className="workspace-content" id="workspace-main" tabIndex={-1}>
      <header className="workspace-top"><div><span className="workspace-crumb">MI ESPACIO <span>/</span> {label(page).toUpperCase()}</span><p>Escuela Profesional de Ciencia de la Computación</p></div><div className="workspace-top-actions"><time className="today-label">{dateLabel}</time><span className="role-chip"><span className="live-dot" />{role}</span><button className="top-account" aria-label="Abrir mi perfil" onClick={() => navigate('Mi perfil')}>{user.nombre[0]}</button></div></header>
      {logoutError && <p className="alert alert-error" role="alert">{logoutError}</p>}
      <div className="workspace-view" key={page}>
      {page === 'Mi perfil' ? <MiPerfilPage onSaved={onUserChange} /> : page === 'Usuarios' ? <UsuarioPage /> : page === 'Equipos' ? <CatalogoPage administrador={user.administrador} onReservar={id => { setSelectedObject(id); navigate('Reservas') }} /> : page === 'Reservas' ? <ReservasPage user={user} objetoInicial={selectedObject} onEntregar={id => { setSelectedReserva(id); navigate('Préstamos') }} /> : page === 'Préstamos' ? <PrestamosPage user={user} reservaInicial={selectedReserva} onReservas={() => navigate('Reservas')} /> : <>
        <section className="workspace-hero"><div className="hero-copy"><span className="hero-eyebrow"><span className="live-dot" />TU PRÓXIMA IDEA EMPIEZA AQUÍ</span><h1>Hola, {user.nombre.split(' ')[0]}<span>¿Qué vamos a crear hoy?</span></h1><p>{user.administrador ? 'Organiza los recursos, acompaña a la comunidad y mantén cada reserva al día.' : 'Los recursos de la escuela, a tu alcance. Encuentra un equipo y dale forma a tu próximo proyecto.'}</p><div className="hero-actions"><button onClick={() => navigate('Equipos')}>Explorar catálogo <span aria-hidden="true">↗</span></button><button onClick={() => navigate('Reservas')}>{user.administrador ? 'Gestionar reservas' : 'Ver mis reservas'} <span aria-hidden="true">→</span></button></div></div><div className="hero-art" aria-hidden="true"><div className="art-orbit" /><span className="art-spark spark-one">+</span><span className="art-spark spark-two">+</span><div className="art-availability"><span className="live-dot" /><div><strong>{loading || error ? '—' : available.length} equipos</strong><small>listos para crear</small></div></div><div className="art-screen"><span /><div>&lt; ideas /&gt;</div><small>EPCC · UNSA</small></div><span className="art-tag">Diseña. Construye. Comparte.</span></div></section>
        <section className="workspace-shortcuts" aria-label="Accesos rápidos">
          <button onClick={() => navigate('Equipos')}><span className="shortcut-icon"><Icon name="Equipos" /></span><span><strong>Encuentra tu equipo</strong><small>Explora lo que tenemos para ti</small></span><b aria-hidden="true">↗</b></button>
          <button onClick={() => navigate('Reservas')}><span className="shortcut-icon"><Icon name="Reservas" /></span><span><strong>{user.administrador ? 'Organiza las reservas' : 'Planea tu proyecto'}</strong><small>El equipo adecuado, en tu fecha</small></span><b aria-hidden="true">↗</b></button>
          <button onClick={() => navigate(user.administrador ? 'Usuarios' : 'Mi perfil')}><span className="shortcut-icon"><Icon name={user.administrador ? 'Usuarios' : 'Mi perfil'} /></span><span><strong>{user.administrador ? 'Conecta a la comunidad' : 'Tu espacio personal'}</strong><small>{user.administrador ? 'Perfiles y accesos de la escuela' : 'Tu información, siempre a mano'}</small></span><b aria-hidden="true">↗</b></button>
        </section>
        <div className="section-heading"><div><span className="section-eyebrow">TODO A LA VISTA</span><h2>Tu espacio en números</h2></div><button className="refresh-button" disabled={loading} onClick={() => void refresh()}><span className={loading ? 'refresh-spin' : ''} aria-hidden="true">↻</span>{loading ? 'Actualizando…' : 'Actualizar'}</button></div>
        {error && <p className="alert alert-error" role="alert">{error} <button onClick={() => void refresh()}>Reintentar</button></p>}
        <section className="workspace-stats" aria-label="Resumen de actividad" aria-busy={loading}>{metrics.map((m, i) => <article className={`metric-card metric-${i}`} key={m.title}><div><span className="metric-icon"><Icon name={m.icon} /></span><span className="metric-label">{m.title}</span></div><strong>{loading ? '—' : error ? '—' : m.count}</strong><small>{m.detail}</small></article>)}</section>
        <div className="dashboard-grid"><section className="panel dashboard-equipment"><div className="section-heading"><div><span className="section-eyebrow">DALE FORMA A TUS IDEAS</span><h2>Listos para llevar</h2></div><button className="text-button" onClick={() => navigate('Equipos')}>Ver catálogo →</button></div>{loading ? <p className="dashboard-empty" role="status">Consultando equipos…</p> : error ? <p className="dashboard-empty">Actualiza los datos para consultar los equipos.</p> : available.length ? available.slice(0, 3).map(o => <div className="equipment-preview" key={o.id}><span className="equipment-symbol"><Icon name="Equipos" /></span><div><strong>{o.nombre}</strong><small>{o.descripcion || 'Equipo de la escuela'}</small></div><button aria-label={`Reservar ${o.nombre}`} onClick={() => { setSelectedObject(o.id); navigate('Reservas') }}>Reservar <span aria-hidden="true">↗</span></button></div>) : <p className="dashboard-empty">Por ahora no hay equipos disponibles. Puedes consultar el catálogo completo.</p>}</section>
        <section className="dashboard-guide"><span className="section-eyebrow">ASÍ DE FÁCIL</span><h2>De la idea<br />{' '}al proyecto.</h2><ol><li><b>01</b><div><strong>Encuentra tu equipo</strong><p>Explora el catálogo y su disponibilidad.</p></div></li><li><b>02</b><div><strong>Elige tus fechas</strong><p>Envía una reserva para tu proyecto.</p></div></li><li><b>03</b><div><strong>Prepara tu próximo paso</strong><p>Consulta la confirmación en tus reservas.</p></div></li></ol><button className="text-button" onClick={() => navigate('Mi perfil')}>Completar mi perfil →</button></section></div>
      </>}
      </div><footer className="workspace-footer"><span>EPCC · UNSA</span><span>Recursos que conectan ideas.</span></footer>
    </main>
  </div>
}
