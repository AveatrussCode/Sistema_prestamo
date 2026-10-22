import { useState } from 'react'
import type { FormEvent } from 'react'
import { login, register } from '../api/auth'
import type { RegistroCuenta, SessionUser } from '../api/auth'
import { subirConstancia } from './usuarioApi'
import './registro.css'
export default function RegistroCuentaForm({ onSuccess, onCancel }: { onSuccess: (user: SessionUser) => void; onCancel: () => void }) {
  const [form, setForm] = useState<RegistroCuenta>({nombre:'',correo:'',codigo:'',tipo:'Estudiante',password:'',especialidad:''})
  const [confirm, setConfirm] = useState('')
  const [visible, setVisible] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [created, setCreated] = useState(false)
  const [account, setAccount] = useState<SessionUser | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError('')
    if (!created && form.password !== confirm) { setError('Las contraseñas no coinciden.'); return }
    setBusy(true)
    try {
      if (!created) { await register(form); setCreated(true) }
      const user=account ?? await login(form.correo,form.password)
      setAccount(user)
      if (form.tipo === 'Estudiante' && file) await subirConstancia(user.id,file)
      onSuccess(user)
    } catch(e) { setError(e instanceof Error ? e.message : 'No se pudo crear tu cuenta.') }
    finally { setBusy(false) }
  }
  return <div className="registro"><h2>Crea tu cuenta</h2><p>Únete al sistema de préstamos de la EPCC.</p>
    <form onSubmit={submit}><fieldset disabled={busy || created}>
      <div className="registro-types" role="group" aria-label="Tipo de cuenta">{(['Estudiante','Profesor'] as const).map(t=><button type="button" key={t} className={form.tipo===t?'active':''} aria-pressed={form.tipo===t} onClick={()=>{setForm({...form,tipo:t});setFile(null)}}>{t}</button>)}</div>
      <label>Nombre completo<input autoFocus required minLength={2} maxLength={150} autoComplete="name" value={form.nombre} onChange={e=>setForm({...form,nombre:e.target.value})} /></label>
      <div className="registro-row"><label>Correo institucional<input type="email" required maxLength={200} autoComplete="username" placeholder="nombre@unsa.edu.pe" value={form.correo} onChange={e=>setForm({...form,correo:e.target.value})} /></label><label>Código institucional<input required maxLength={50} value={form.codigo} onChange={e=>setForm({...form,codigo:e.target.value})} /></label></div>
      {form.tipo==='Profesor' && <label>Especialidad<input maxLength={150} placeholder="Ej. Ingeniería de Software" value={form.especialidad} onChange={e=>setForm({...form,especialidad:e.target.value})} /></label>}
      <div className="registro-row"><label>Contraseña<div className="login-password"><input required minLength={8} maxLength={128} autoComplete="new-password" type={visible?'text':'password'} placeholder="Mínimo 8 caracteres" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} /><button type="button" aria-label={visible?'Ocultar contraseña':'Mostrar contraseña'} aria-pressed={visible} onClick={()=>setVisible(!visible)}><span aria-hidden="true">{visible?'🙉':'🙈'}</span></button></div></label><label>Confirma tu contraseña<input required minLength={8} maxLength={128} autoComplete="new-password" type={visible?'text':'password'} value={confirm} onChange={e=>setConfirm(e.target.value)} /></label></div>
      <small>Escuela Profesional de Ciencia de la Computación · UNSA</small>
    </fieldset>
    {form.tipo==='Estudiante' && <label className="registro-pdf">Constancia de matrícula (PDF)<input disabled={busy} type="file" accept=".pdf,application/pdf" onChange={e=>{const f=e.target.files?.[0];setFile(null);if(!f)return;if(!f.name.toLowerCase().endsWith('.pdf')||f.size>5*1024*1024){setError('Selecciona un PDF de hasta 5 MB.');e.target.value='';return}setError('');setFile(f)}} /><small>{file?file.name:'Opcional al registrarte. Puedes adjuntarla después en Mi perfil. Máximo 5 MB.'}</small></label>}
    {created && error && <p className="registro-info">Tu cuenta ya fue creada. Puedes reintentar sin volver a registrarte.</p>}
    {error && <p className="login-error" role="alert">{error}</p>}
    <button className="login-submit" disabled={busy}>{busy?'Guardando tu cuenta…':created?'Continuar con mi cuenta':'Crear cuenta →'}</button>
    {account && error && <button className="registro-back" type="button" disabled={busy} onClick={()=>onSuccess(account)}>Entrar y adjuntar la constancia después</button>}
    </form>
    {!created && <button type="button" className="registro-back" disabled={busy} onClick={onCancel}>¿Ya tienes cuenta? Inicia sesión</button>}
    <small className="registro-admin">Las cuentas administrativas las habilita el administrador.</small>
  </div>
}
