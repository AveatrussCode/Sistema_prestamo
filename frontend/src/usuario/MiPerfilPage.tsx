import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { obtenerPerfil, guardarPerfil } from '../api/auth'
import type { MiPerfil, SessionUser } from '../api/auth'
import { subirConstancia, constanciaUrl } from './usuarioApi'
import './perfil.css'
export default function MiPerfilPage({ onSaved }: { onSaved: (user: SessionUser) => void }) {
  const [profile,setProfile]=useState<MiPerfil | null>(null)
  const [nombre,setNombre]=useState('')
  const [especialidad,setEspecialidad]=useState('')
  const [file,setFile]=useState<File | null>(null)
  const [error,setError]=useState('')
  const [notice,setNotice]=useState('')
  const [busy,setBusy]=useState(false)
  useEffect(()=>{let active=true;obtenerPerfil().then(p=>{if(active){setProfile(p);setNombre(p.nombre);setEspecialidad(p.especialidad ?? '')}}).catch(e=>{if(active)setError(e instanceof Error?e.message:'No se pudo cargar el perfil.')});return()=>{active=false}},[])
  async function save(e:FormEvent<HTMLFormElement>){
    e.preventDefault();if(!profile)return;setBusy(true);setError('');setNotice('')
    try{
      await guardarPerfil({nombre:nombre.trim(),especialidad})
      if(file && profile.tipo==='estudiante') await subirConstancia(profile.id,file)
      const p=await obtenerPerfil();setProfile(p);onSaved(p);setFile(null);setNotice('Tu información se guardó correctamente.')
    }catch(e){setError(e instanceof Error?e.message:'No se pudo guardar. Puedes reintentar.')}
    finally{setBusy(false)}
  }
  return <section className="perfil-page"><header><span className="usuario-eyebrow">MI CUENTA · EPCC</span><h1>Mi perfil</h1><p>Actualiza tus datos y consulta tu información institucional.</p></header>{error && <p className="usuario-error" role="alert">{error}</p>}{notice && <p className="usuario-success" role="status">{notice}</p>}
    {!profile ? <p>{error?'No se pudo cargar el perfil.':'Cargando tu información…'}</p> : <div className="perfil-layout"><aside className="perfil-card"><span className="perfil-avatar">{profile.nombre[0]?.toUpperCase()}</span><h2>{profile.nombre}</h2><span className="perfil-role">{profile.administrador?'Administrador':profile.tipo==='profesor'?'Profesor':'Estudiante'}</span><p>{profile.correo}</p><dl><dt>Código institucional</dt><dd>{profile.codigo}</dd><dt>Escuela</dt><dd>Ciencia de la Computación</dd>{!profile.administrador && <><dt>Confiabilidad</dt><dd>{profile.credibilidad}/100</dd></>}</dl></aside><form className="perfil-form" onSubmit={save}><h2>{profile.tipo==='profesor'?'Información docente':profile.administrador?'Información administrativa':'Información del estudiante'}</h2><label>Nombre completo<input required minLength={2} maxLength={150} value={nombre} onChange={e=>setNombre(e.target.value)} /></label><label>Correo institucional<input disabled value={profile.correo} /></label>{profile.tipo==='profesor' && <><label>Departamento<input disabled value={profile.departamento ?? 'Ciencia de la Computación'} /></label><label>Especialidad<input maxLength={150} value={especialidad} onChange={e=>setEspecialidad(e.target.value)} /></label></>}{profile.administrador && <p className="perfil-help">Tu cuenta permite gestionar usuarios, asignar roles y administrar reservas.</p>}
    {profile.tipo==='estudiante' && <div className="perfil-pdf"><h3>Constancia de matrícula</h3><p>{profile.constancia_matricula?'Tienes una constancia guardada. Puedes descargarla o reemplazarla.':'Aún no has adjuntado tu constancia de matrícula.'}</p>{profile.constancia_matricula && <a href={constanciaUrl(profile.id)} target="_blank" rel="noreferrer">Descargar mi constancia PDF</a>}<label>Adjuntar PDF (máximo 5 MB)<input key={profile.constancia_matricula && !file ? 'guardado' : 'nuevo'} type="file" disabled={busy} accept=".pdf,application/pdf" onChange={e=>{const f=e.target.files?.[0];setFile(null);if(!f)return;if(!f.name.toLowerCase().endsWith('.pdf')||f.size>5*1024*1024){setError('Selecciona un PDF de hasta 5 MB.');e.target.value='';return}setError('');setFile(f)}} /></label></div>}
    <button className="usuario-primary" disabled={busy}>{busy?'Guardando…':'Guardar mi información'}</button></form></div>}
  </section>
}
