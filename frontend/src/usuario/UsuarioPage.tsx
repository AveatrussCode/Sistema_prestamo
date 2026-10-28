import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  subirConstancia, constanciaUrl, listarUsuarios, crearUsuario, editarUsuario,
  cambiarEstado, eliminarUsuario, listarRoles, asignarRol, ajustarCredibilidad,
  listarSolicitudes, contarSolicitudes, aprobarSolicitud, rechazarSolicitud
} from './usuarioApi'
import type { Usuario, NuevoUsuario, TipoUsuario, EstadoUsuario, Rol, SolicitudPendiente } from './usuarioApi'
import './usuario.css'

const mensaje = (e: unknown) => e instanceof Error ? e.message : 'No se pudo completar la operación.'
const vacio: NuevoUsuario = { nombre: '', correo: '', codigo: '', tipo: 'Estudiante', password: '' }

export default function UsuarioPage() {
  // ---- Estados base ----
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [roles, setRoles] = useState<Rol[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [search, setSearch] = useState('')
  const [tipo, setTipo] = useState('Todos')
  const [estado, setEstado] = useState('Todos')
  const [form, setForm] = useState<NuevoUsuario>(vacio)
  const [pdf, setPdf] = useState<File | null>(null)
  const [editing, setEditing] = useState<Usuario | null>(null)
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [selected, setSelected] = useState<Usuario | null>(null)
  const [action, setAction] = useState<'estado' | 'rol' | 'credibilidad' | 'eliminar'>('estado')
  const [value, setValue] = useState('')
  const [reason, setReason] = useState('')

  // ---- Estados del flujo de aprobación ----
  const [tab, setTab] = useState<'usuarios' | 'solicitudes'>('usuarios')
  const [solicitudes, setSolicitudes] = useState<SolicitudPendiente[]>([])
  const [pendientes, setPendientes] = useState(0)
  const [rechazo, setRechazo] = useState<SolicitudPendiente | null>(null)
  const [motivo, setMotivo] = useState('')
  const [solicitudesLoading, setSolicitudesLoading] = useState(false)

  // ---- Carga de datos ----
  async function load() {
    setLoading(true); setError('')
    try {
      const [u, r, c] = await Promise.all([listarUsuarios(), listarRoles(), contarSolicitudes()])
      setUsuarios(u); setRoles(r); setPendientes(c.total)
    } catch (e) {
      setError(mensaje(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let active = true
    Promise.all([listarUsuarios(), listarRoles(), contarSolicitudes()])
      .then(([u, r, c]) => {
        if (active) { setUsuarios(u); setRoles(r); setPendientes(c.total) }
      })
      .catch(e => { if (active) setError(mensaje(e)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (tab !== 'solicitudes') return
    setSolicitudesLoading(true)
    listarSolicitudes()
      .then(setSolicitudes)
      .catch(e => setError(mensaje(e)))
      .finally(() => setSolicitudesLoading(false))
  }, [tab])

  // ---- CRUD de usuarios ----
  function newUser() {
    setPdf(null); setEditing(null); setForm({ ...vacio }); setError(''); setNotice(''); setOpen(true)
  }

  function edit(u: Usuario) {
    setPdf(null); setEditing(u)
    setForm({
      nombre: u.nombre, correo: u.correo, codigo: u.codigo,
      tipo: (u.tipo === 'estudiante' ? 'Estudiante' : u.tipo === 'profesor' ? 'Profesor' : 'Administrativo')
    })
    setError(''); setNotice(''); setOpen(true)
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(''); setNotice('')
    try {
      const datos = { ...form, nombre: form.nombre.trim(), correo: form.correo.trim(), codigo: form.codigo.trim() }
      if (!datos.nombre || !datos.correo || !datos.codigo) throw new Error('Completa los campos obligatorios.')
      
      if (editing) await editarUsuario(editing.id, { nombre: datos.nombre, correo: datos.correo })
      
      let id = editing?.id
      if (!editing) {
        const creado = await crearUsuario({ ...datos, ...(datos.tipo === 'Estudiante' ? { carrera: 'Ciencia de la Computación' } : {}) })
        id = creado.id
        setEditing({ id, nombre: datos.nombre, correo: datos.correo, codigo: datos.codigo, tipo: datos.tipo.toLowerCase(), estado: 'ACTIVO', credibilidad: 100, rol: null })
      }
      
      if (pdf && id !== undefined && datos.tipo === 'Estudiante') {
        try { await subirConstancia(id, pdf) }
        catch (e) { throw new Error(`El perfil se guardó, pero no la constancia. Guarda nuevamente para reintentar. ${mensaje(e)}`) }
      }
      
      setForm({ ...vacio }); setOpen(false); 
      setNotice(editing ? 'Perfil actualizado correctamente.' : 'Usuario registrado correctamente.')
      await load()
    } catch (e) {
      setError(mensaje(e))
    } finally {
      setBusy(false)
    }
  }

  function manage(u: Usuario, a: typeof action) {
    setSelected(u); setAction(a); setError(''); setNotice(''); setReason('')
    setValue(
      a === 'estado' ? u.estado ?? 'ACTIVO' : 
      a === 'credibilidad' ? String(u.credibilidad) : 
      String(roles.find(r => r.nombre === u.rol)?.id ?? roles[0]?.id ?? '')
    )
  }

  async function apply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return
    setBusy(true); setError(''); setNotice('')
    try {
      if (action === 'estado') await cambiarEstado(selected.id, value as EstadoUsuario)
      if (action === 'rol') await asignarRol(selected.id, Number(value))
      if (action === 'credibilidad') await ajustarCredibilidad(selected.id, Number(value), reason.trim())
      if (action === 'eliminar') await eliminarUsuario(selected.id)
      setSelected(null); setNotice('Cambio guardado correctamente.'); await load()
    } catch (e) {
      setError(mensaje(e))
    } finally {
      setBusy(false)
    }
  }

  // ---- Acciones de aprobación ----
  async function handleAprobar(s: SolicitudPendiente) {
    if (!s.verificado_externo && !confirm('Este usuario no fue verificado automáticamente por el sistema externo. ¿Aprobar de todas formas?')) return
    setBusy(true); setError(''); setNotice('')
    try {
      await aprobarSolicitud(s.id, !s.verificado_externo)
      setSolicitudes(solicitudes.filter(x => x.id !== s.id))
      setPendientes(p => Math.max(0, p - 1))
      setNotice(`Usuario ${s.nombre} aprobado correctamente.`)
      await load()
    } catch (e) {
      setError(mensaje(e))
    } finally {
      setBusy(false)
    }
  }

  async function handleRechazar() {
    if (!rechazo || motivo.trim().length < 10) return
    setBusy(true); setError(''); setNotice('')
    try {
      await rechazarSolicitud(rechazo.id, motivo.trim())
      setSolicitudes(solicitudes.filter(x => x.id !== rechazo.id))
      setPendientes(p => Math.max(0, p - 1))
      setNotice(`Solicitud de ${rechazo.nombre} rechazada.`)
      setRechazo(null); setMotivo('')
    } catch (e) {
      setError(mensaje(e))
    } finally {
      setBusy(false)
    }
  }

  // ---- Filtros y utilidades ----
  const filtered = usuarios.filter(u => 
    `${u.nombre} ${u.correo} ${u.codigo}`.toLowerCase().includes(search.toLowerCase()) && 
    (tipo === 'Todos' || u.tipo === tipo) && 
    (estado === 'Todos' || u.estado === estado)
  )
  const extras = form.tipo === 'Estudiante' ? [] : form.tipo === 'Profesor' ? ['departamento','especialidad'] : ['area','cargo']
  const labels: Record<string,string> = { matricula:'Matrícula', departamento:'Departamento', especialidad:'Especialidad', area:'Área', cargo:'Cargo' }
  const actionLabels = { estado:'Cambiar estado', rol:'Asignar rol', credibilidad:'Ajustar confiabilidad', eliminar:'Eliminar usuario' }
  const close = () => { if (!busy) { setOpen(false); setSelected(null); setError('') } }

  return (
    <section className="usuario-page">
      <header className="usuario-heading">
        <div>
          <span className="usuario-eyebrow">COMUNIDAD EPCC</span>
          <h1>Usuarios</h1>
          <p>Administra perfiles, roles y aprobaciones.</p>
        </div>
        <button className="usuario-primary" onClick={newUser}>+ Registrar usuario</button>
      </header>

      {/* --- Pestañas --- */}
      <div className="usuario-tabs" style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '10px' }}>
        <button 
          className={tab === 'usuarios' ? 'active' : ''} 
          onClick={() => setTab('usuarios')}
          style={{ background: 'none', border: 'none', borderBottom: tab === 'usuarios' ? '2px solid #0754b5' : 'none', padding: '8px 12px', cursor: 'pointer', fontWeight: tab === 'usuarios' ? 600 : 400, color: tab === 'usuarios' ? '#0754b5' : '#64748b' }}
        >
          Usuarios activos
        </button>
        <button 
          className={tab === 'solicitudes' ? 'active' : ''} 
          onClick={() => setTab('solicitudes')}
          style={{ background: 'none', border: 'none', borderBottom: tab === 'solicitudes' ? '2px solid #0754b5' : 'none', padding: '8px 12px', cursor: 'pointer', fontWeight: tab === 'solicitudes' ? 600 : 400, color: tab === 'solicitudes' ? '#0754b5' : '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          Solicitudes
          {pendientes > 0 && (
            <span style={{ background: '#e11d48', color: 'white', borderRadius: '12px', padding: '2px 6px', fontSize: '10px', fontWeight: 'bold' }}>
              {pendientes}
            </span>
          )}
        </button>
      </div>

      {!open && !selected && !rechazo && error && <p className="usuario-error" role="alert">{error}</p>}
      {notice && <p className="usuario-success" role="status">{notice}</p>}

      {/* --- VISTA: USUARIOS ACTIVOS --- */}
      {tab === 'usuarios' && (
        <>
          <div className="usuario-stats">
            <article><span>Total de usuarios</span><strong>{loading ? '…' : usuarios.length}</strong></article>
            <article><span>Usuarios activos</span><strong>{loading ? '…' : usuarios.filter(u=>u.estado==='ACTIVO').length}</strong></article>
            <article><span>Estudiantes</span><strong>{loading ? '…' : usuarios.filter(u=>u.tipo==='estudiante').length}</strong></article>
          </div>
          
          <div className="usuario-list">
            <div className="usuario-toolbar">
              <input aria-label="Buscar usuarios" placeholder="Buscar por nombre, correo o código…" value={search} onChange={e=>setSearch(e.target.value)} />
              <select aria-label="Filtrar por tipo" value={tipo} onChange={e=>setTipo(e.target.value)}>
                <option>Todos</option>
                <option value="estudiante">Estudiantes</option>
                <option value="profesor">Profesores</option>
                <option value="administrativo">Administrativos</option>
              </select>
              <select aria-label="Filtrar por estado" value={estado} onChange={e=>setEstado(e.target.value)}>
                <option>Todos</option>
                {['ACTIVO','INACTIVO','SUSPENDIDO', 'PENDIENTE_APROBACION'].map(s=><option key={s}>{s}</option>)}
              </select>
              <button onClick={()=>void load()} disabled={loading}>{loading?'Cargando…':'Actualizar'}</button>
            </div>
            
            <div className="usuario-table">
              <table>
                <thead>
                  <tr><th>Usuario</th><th>Código / Tipo</th><th>Rol</th><th>Estado</th><th>Confiabilidad</th><th>Acciones</th></tr>
                </thead>
                <tbody>
                  {filtered.map(u=>(
                    <tr key={u.id}>
                      <td>
                        <div className="usuario-identity">
                          <span className="usuario-avatar" aria-hidden="true">{u.nombre.slice(0,1).toUpperCase()}</span>
                          <div><strong>{u.nombre}</strong><small>{u.correo}</small></div>
                        </div>
                      </td>
                      <td><strong>{u.codigo}</strong><small>{u.tipo}</small></td>
                      <td>{u.rol ?? 'Sin asignar'}</td>
                      <td><span className={`usuario-badge ${u.estado?.toLowerCase()}`}>{u.estado ?? 'Sin estado'}</span></td>
                      <td><span>{u.credibilidad}/100</span><meter min="0" max="100" value={u.credibilidad} aria-label={`Confiabilidad de ${u.nombre}`} /></td>
                      <td>
                        <div className="usuario-actions">
                          <button onClick={()=>edit(u)}>Editar</button>
                          {u.constancia_matricula && (
                            <button onClick={() => window.open(constanciaUrl(u.id), '_blank')}>
                              PDF matrícula
                            </button>
                          )}
                          <button onClick={()=>manage(u,'estado')}>Estado</button>
                          <button onClick={()=>manage(u,'rol')}>Rol</button>
                          <button onClick={()=>manage(u,'credibilidad')}>Confiabilidad</button>
                          <button className="usuario-danger" onClick={()=>manage(u,'eliminar')}>Eliminar</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {!loading && filtered.length===0 && (
              <div className="usuario-empty">
                <strong>{usuarios.length ? 'No hay coincidencias' : 'Aún no hay usuarios registrados'}</strong>
                <p>{usuarios.length ? 'Prueba con otro nombre o ajusta los filtros.' : 'Registra el primer usuario para empezar a gestionar reservas.'}</p>
                {!usuarios.length && <button className="usuario-primary" onClick={newUser}>Registrar primer usuario</button>}
              </div>
            )}
            <footer>{loading?'Consultando usuarios…':`${filtered.length} de ${usuarios.length} usuarios`}</footer>
          </div>
        </>
      )}

      {/* --- VISTA: SOLICITUDES PENDIENTES --- */}
      {tab === 'solicitudes' && (
        <div className="usuario-list">
          <div style={{ padding: '0 0 15px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '18px', margin: 0 }}>Solicitudes pendientes ({solicitudes.length})</h2>
            <button onClick={() => {
              setSolicitudesLoading(true)
              listarSolicitudes().then(setSolicitudes).catch(e=>setError(mensaje(e))).finally(()=>setSolicitudesLoading(false))
            }} disabled={solicitudesLoading}>
              {solicitudesLoading ? 'Cargando…' : 'Actualizar'}
            </button>
          </div>

          {solicitudes.length === 0 ? (
            <div className="usuario-empty">
              <strong>No hay solicitudes pendientes</strong>
              <p>Todas las cuentas han sido revisadas.</p>
            </div>
          ) : (
            <div className="usuario-table">
              <table>
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>Tipo</th>
                    <th>Fecha</th>
                    <th>Constancia</th>
                    <th>Verif. Externa</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {solicitudes.map(s => (
                    <tr key={s.id}>
                      <td>
                        <div className="usuario-identity">
                          <span className="usuario-avatar" aria-hidden="true">{s.nombre.slice(0,1).toUpperCase()}</span>
                          <div><strong>{s.nombre}</strong><small>{s.correo}<br/>{s.codigo}</small></div>
                        </div>
                      </td>
                      <td>
                        <strong style={{ textTransform: 'capitalize' }}>{s.tipo}</strong>
                        <small>{s.detalles.especialidad || s.detalles.area || s.detalles.carrera || ''}</small>
                      </td>
                      <td>{s.fecha_solicitud ? new Date(s.fecha_solicitud).toLocaleString('es-PE') : '—'}</td>
                      <td>
                        {s.constancia_matricula 
                          ? <a href={constanciaUrl(s.id)} target="_blank" rel="noreferrer" style={{ display: 'inline-block', padding: '6px 10px', border: '1px solid #dce6f1', borderRadius: '6px', color: '#507298', textDecoration: 'none', fontSize: '12px', background: '#fff' }}>PDF matrícula</a>
                          : <span style={{ color: '#94a3b8' }}>—</span>}
                      </td>
                      <td>
                        {s.verificado_externo 
                          ? <span title="Verificado" style={{ color: '#16a34a', fontSize: '18px' }}>✅</span> 
                          : <span title="No verificado por sistema externo" style={{ color: '#eab308', fontSize: '18px' }}>⚠️</span>}
                      </td>
                      <td>
                        <div className="usuario-actions">
                          <button onClick={() => handleAprobar(s)} style={{ background: '#dcfce7', color: '#166534', borderColor: '#bbf7d0' }}>Aprobar</button>
                          <button className="usuario-danger" onClick={() => { setRechazo(s); setMotivo(''); }}>Rechazar</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* --- MODALES EXISTENTES (Crear/Editar y Acciones) --- */}
      {(open || selected) && !rechazo && (
        <div className="usuario-overlay" onKeyDown={e=>{if(e.key==='Escape') close()}}>
          <section className="usuario-modal" role="dialog" aria-modal="true" aria-labelledby="usuario-dialog-title">
            <header>
              <div>
                <span className="usuario-eyebrow">GESTIÓN DE USUARIOS</span>
                <h2 id="usuario-dialog-title">{open ? (editing ? 'Editar perfil' : 'Registrar usuario') : actionLabels[action]}</h2>
              </div>
              <button type="button" aria-label="Cerrar" disabled={busy} onClick={close}>×</button>
            </header>
            {error && <p className="usuario-error" role="alert">{error}</p>}
            
            {open ? (
              <form onSubmit={save}>
                <label>Nombre completo<input autoFocus required maxLength={150} value={form.nombre} onChange={e=>setForm({...form,nombre:e.target.value})} /></label>
                <label>Correo institucional<input type="email" required maxLength={200} value={form.correo} onChange={e=>setForm({...form,correo:e.target.value})} /></label>
                {!editing && (
                  <>
                    <div className="usuario-form-row">
                      <label>Código institucional<input required maxLength={50} value={form.codigo} onChange={e=>setForm({...form,codigo:e.target.value})} /></label>
                      <label>Tipo de usuario
                        <select value={form.tipo} onChange={e=>{setPdf(null);setForm({...vacio,nombre:form.nombre,correo:form.correo,codigo:form.codigo,tipo:e.target.value as TipoUsuario})}}>
                          {['Estudiante','Profesor','Administrativo'].map(t=><option key={t}>{t}</option>)}
                        </select>
                      </label>
                    </div>
                    <div className="usuario-form-row">
                      {extras.map(key=><label key={key}>{labels[key]}<input value={form[key as keyof NuevoUsuario] ?? ''} onChange={e=>setForm({...form,[key]:e.target.value})} /></label>)}
                    </div>
                    <label>Contraseña inicial
                      <input type="password" required minLength={8} maxLength={128} autoComplete="new-password" value={form.password ?? ''} onChange={e=>setForm({...form,password:e.target.value})} />
                      <small>Mínimo 8 caracteres. Compártela con el usuario para que pueda iniciar sesión.</small>
                    </label>
                    <p className="usuario-help">El rol inicial se asigna según el tipo de usuario.</p>
                  </>
                )}
                
                {form.tipo === 'Estudiante' && (
                  <div className="usuario-upload">
                    <label>Constancia de matrícula (PDF)
                      <input type="file" accept=".pdf,application/pdf" onChange={e=>{
                        const file=e.target.files?.[0];setPdf(null);
                        if(!file)return;
                        if(!file.name.toLowerCase().endsWith('.pdf') || file.size > 5*1024*1024){setError('Selecciona un PDF de hasta 5 MB.');e.target.value='';return}
                        setError('');setPdf(file)
                      }} />
                    </label>
                    <small>{pdf ? `Archivo seleccionado: ${pdf.name}` : 'Adjunta la constancia de matrícula. Máximo 5 MB.'}</small>
                    {editing?.constancia_matricula && <a href={constanciaUrl(editing.id)} target="_blank" rel="noreferrer">Descargar constancia actual</a>}
                  </div>
                )}
                
                <div className="usuario-modal-actions">
                  <button type="button" onClick={close} disabled={busy}>Cancelar</button>
                  <button className="usuario-primary" disabled={busy}>{busy?'Guardando…':editing?'Guardar cambios':'Registrar usuario'}</button>
                </div>
              </form>
            ) : selected && (
              <form onSubmit={apply}>
                <p className="usuario-target">{selected.nombre} · {selected.correo}</p>
                {action==='estado' && (
                  <label>Estado
                    <select autoFocus value={value} onChange={e=>setValue(e.target.value)}>
                      {['ACTIVO','INACTIVO','SUSPENDIDO'].map(s=><option key={s}>{s}</option>)}
                    </select>
                  </label>
                )}
                {action==='rol' && (
                  <label>Rol
                    <select autoFocus required value={value} onChange={e=>setValue(e.target.value)}>
                      <option value="">Selecciona un rol</option>
                      {roles.map(r=><option key={r.id} value={r.id}>{r.nombre}</option>)}
                    </select>
                  </label>
                )}
                {action==='credibilidad' && (
                  <>
                    <label>Confiabilidad (0 a 100)
                      <input autoFocus type="number" required min="0" max="100" step="0.1" value={value} onChange={e=>setValue(e.target.value)} />
                    </label>
                    <label>Motivo del ajuste
                      <input required pattern=".*\S.*" value={reason} onChange={e=>setReason(e.target.value)} />
                    </label>
                  </>
                )}
                {action==='eliminar' && <p>¿Eliminar este usuario de forma permanente? Esta acción no se puede deshacer.</p>}
                <div className="usuario-modal-actions">
                  <button autoFocus={action==='eliminar'} type="button" disabled={busy} onClick={close}>Cancelar</button>
                  <button className={action==='eliminar'?'usuario-delete':'usuario-primary'} disabled={busy}>
                    {busy?'Guardando…':action==='eliminar'?'Eliminar usuario':'Guardar cambios'}
                  </button>
                </div>
              </form>
            )}
          </section>
        </div>
      )}

      {/* --- MODAL DE RECHAZO --- */}
      {rechazo && (
        <div className="usuario-overlay">
          <section className="usuario-modal" role="dialog" aria-modal="true" aria-labelledby="rechazo-dialog-title">
            <header>
              <div>
                <span className="usuario-eyebrow">RECHAZAR SOLICITUD</span>
                <h2 id="rechazo-dialog-title">Rechazar cuenta</h2>
              </div>
              <button type="button" disabled={busy} onClick={() => setRechazo(null)}>×</button>
            </header>
            
            <p>Vas a rechazar la solicitud de <strong>{rechazo.nombre}</strong> ({rechazo.correo}).</p>
            
            <label>Motivo del rechazo (obligatorio, mínimo 10 caracteres)
              <textarea 
                required minLength={10} maxLength={500} rows={4}
                autoFocus
                value={motivo} 
                onChange={e => setMotivo(e.target.value)}
                placeholder="Ej. La constancia adjunta está vencida o no coincide con el nombre registrado."
              />
            </label>
            
            <div className="usuario-modal-actions">
              <button type="button" onClick={() => setRechazo(null)} disabled={busy}>Cancelar</button>
              <button 
                className="usuario-delete" 
                disabled={busy || motivo.trim().length < 10}
                onClick={handleRechazar}
              >
                {busy ? 'Procesando…' : 'Rechazar y notificar'}
              </button>
            </div>
          </section>
        </div>
      )}
    </section>
  )
}