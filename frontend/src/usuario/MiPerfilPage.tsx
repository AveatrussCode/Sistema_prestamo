import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { obtenerPerfil, guardarPerfil, cambiarPassword } from '../api/auth'
import type { MiPerfil, SessionUser } from '../api/auth'
import { subirConstancia, constanciaUrl } from './usuarioApi'
import './perfil.css'

export default function MiPerfilPage({ onSaved }: { onSaved: (user: SessionUser) => void }) {
  // Estados del perfil
  const [profile, setProfile] = useState<MiPerfil | null>(null)
  const [nombre, setNombre] = useState('')
  const [especialidad, setEspecialidad] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  // Estados para cambiar contraseña
  const [passActual, setPassActual] = useState('')
  const [passNueva, setPassNueva] = useState('')
  const [passConfirm, setPassConfirm] = useState('')
  const [passBusy, setPassBusy] = useState(false)
  const [passMsg, setPassMsg] = useState('')
  const [passError, setPassError] = useState('')

  useEffect(() => {
    let active = true
    obtenerPerfil().then(p => {
      if (active) {
        setProfile(p)
        setNombre(p.nombre)
        setEspecialidad(p.especialidad ?? '')
      }
    }).catch(e => {
      if (active) setError(e instanceof Error ? e.message : 'No se pudo cargar el perfil.')
    })
    return () => { active = false }
  }, [])

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!profile) return
    setBusy(true); setError(''); setNotice('')
    try {
      await guardarPerfil({ nombre: nombre.trim(), especialidad })
      if (file && profile.tipo === 'estudiante') await subirConstancia(profile.id, file)
      
      const p = await obtenerPerfil()
      setProfile(p)
      onSaved(p)
      setFile(null)
      setNotice('Tu información se guardó correctamente.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo guardar. Puedes reintentar.')
    } finally {
      setBusy(false)
    }
  }

  async function cambiarMiPassword(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setPassError(''); setPassMsg('')
    
    if (passNueva !== passConfirm) {
      setPassError('Las contraseñas nuevas no coinciden.')
      return
    }
    if (passNueva.length < 8) {
      setPassError('La nueva contraseña debe tener al menos 8 caracteres.')
      return
    }

    setPassBusy(true)
    try {
      await cambiarPassword(passActual, passNueva)
      setPassMsg('Contraseña actualizada correctamente.')
      setPassActual('')
      setPassNueva('')
      setPassConfirm('')
    } catch (e) {
      setPassError(e instanceof Error ? e.message : 'No se pudo cambiar la contraseña.')
    } finally {
      setPassBusy(false)
    }
  }

  return (
    <section className="perfil-page">
      <header>
        <span className="usuario-eyebrow">MI CUENTA · EPCC</span>
        <h1>Mi perfil</h1>
        <p>Actualiza tus datos y consulta tu información institucional.</p>
      </header>

      {!profile ? (
        <p>{error ? 'No se pudo cargar el perfil.' : 'Cargando tu información…'}</p>
      ) : (
        <div className="perfil-layout">
          
          {/* --- COLUMNA IZQUIERDA: Tarjeta de presentación --- */}
          <aside className="perfil-card">
            <span className="perfil-avatar">{profile.nombre[0]?.toUpperCase()}</span>
            <h2>{profile.nombre}</h2>
            <span className="perfil-role">
              {profile.administrador ? 'Administrador' : profile.tipo === 'profesor' ? 'Profesor' : 'Estudiante'}
            </span>
            <p>{profile.correo}</p>
            <dl>
              <dt>Código institucional</dt>
              <dd>{profile.codigo}</dd>
              <dt>Escuela</dt>
              <dd>Ciencia de la Computación</dd>
              {!profile.administrador && (
                <>
                  <dt>Confiabilidad</dt>
                  <dd>{profile.credibilidad}/100</dd>
                </>
              )}
            </dl>
          </aside>

          {/* --- COLUMNA DERECHA: Formularios --- */}
          <div className="perfil-forms-container">
            
            {/* FORMULARIO 1: Datos del perfil */}
            <form className="perfil-form" onSubmit={save}>
              <h2>
                {profile.tipo === 'profesor' ? 'Información docente' : profile.administrador ? 'Información administrativa' : 'Información del estudiante'}
              </h2>
              
              {error && <p className="usuario-error" role="alert">{error}</p>}
              {notice && <p className="usuario-success" role="status">{notice}</p>}
              
              <label>Nombre completo
                <input required minLength={2} maxLength={150} value={nombre} onChange={e => setNombre(e.target.value)} />
              </label>
              
              <label>Correo institucional
                <input disabled value={profile.correo} />
              </label>

              {profile.tipo === 'profesor' && (
                <>
                  <label>Departamento
                    <input disabled value={profile.departamento ?? 'Ciencia de la Computación'} />
                  </label>
                  <label>Especialidad
                    <input maxLength={150} value={especialidad} onChange={e => setEspecialidad(e.target.value)} />
                  </label>
                </>
              )}

              {profile.administrador && (
                <p className="perfil-help">Tu cuenta permite gestionar usuarios, asignar roles y administrar reservas.</p>
              )}

              {profile.tipo === 'estudiante' && (
                <div className="perfil-pdf">
                  <h3>Constancia de matrícula</h3>
                  <p>{profile.constancia_matricula ? 'Tienes una constancia guardada. Puedes descargarla o reemplazarla.' : 'Aún no has adjuntado tu constancia de matrícula.'}</p>
                  {profile.constancia_matricula && (
                    <a href={constanciaUrl(profile.id)} target="_blank" rel="noreferrer">Descargar mi constancia PDF</a>
                  )}
                  <label>Adjuntar PDF (máximo 5 MB)
                    <input 
                      key={profile.constancia_matricula && !file ? 'guardado' : 'nuevo'} 
                      type="file" 
                      disabled={busy} 
                      accept=".pdf,application/pdf" 
                      onChange={e => {
                        const f = e.target.files?.[0]
                        setFile(null)
                        if (!f) return
                        if (!f.name.toLowerCase().endsWith('.pdf') || f.size > 5 * 1024 * 1024) {
                          setError('Selecciona un PDF de hasta 5 MB.')
                          e.target.value = ''
                          return
                        }
                        setError('')
                        setFile(f)
                      }} 
                    />
                  </label>
                </div>
              )}

              <button className="usuario-primary" disabled={busy}>
                {busy ? 'Guardando…' : 'Guardar mi información'}
              </button>
            </form>

            {/* FORMULARIO 2: Seguridad / Contraseña */}
            <form className="perfil-form" onSubmit={cambiarMiPassword}>
              <h2>Seguridad</h2>
              <p className="perfil-help" style={{ marginTop: '-10px', marginBottom: '10px' }}>
                Actualiza tu contraseña periódicamente para mantener tu cuenta segura.
              </p>
              
              {passError && <p className="usuario-error" role="alert">{passError}</p>}
              {passMsg && <p className="usuario-success" role="status">{passMsg}</p>}

              <label>Contraseña actual
                <input 
                  type="password" 
                  required 
                  value={passActual} 
                  onChange={e => setPassActual(e.target.value)} 
                  autoComplete="current-password" 
                />
              </label>
              
              <label>Nueva contraseña (mínimo 8 caracteres)
                <input 
                  type="password" 
                  required 
                  minLength={8} 
                  value={passNueva} 
                  onChange={e => setPassNueva(e.target.value)} 
                  autoComplete="new-password" 
                />
              </label>
              
              <label>Confirmar nueva contraseña
                <input 
                  type="password" 
                  required 
                  minLength={8} 
                  value={passConfirm} 
                  onChange={e => setPassConfirm(e.target.value)} 
                  autoComplete="new-password" 
                />
              </label>
              
              <button type="submit" className="usuario-primary" disabled={passBusy} style={{ alignSelf: 'flex-start', marginTop: '5px' }}>
                {passBusy ? 'Actualizando…' : 'Cambiar contraseña'}
              </button>
            </form>

          </div>
        </div>
      )}
    </section>
  )
}