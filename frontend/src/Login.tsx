import RegistroCuentaForm from './usuario/RegistroCuentaForm'
import { login, me, logout } from './api/auth'
import type { SessionUser } from './api/auth'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import Workspace from './Workspace'
import './App.css'
import './Login.css'

export default function Login() {
  const [session, setSession] = useState<SessionUser | null>(null)
  const [registering, setRegistering] = useState(false)
  const [busy, setBusy] = useState(false)
  useEffect(() => { void me().then(setSession).catch(() => {}) }, [])
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [visible, setVisible] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true)
    try { setSession(await login(email, password)); setPassword('') }
    catch(e) { setError(e instanceof Error ? e.message : 'No se pudo iniciar sesión.') }
    finally { setBusy(false) }
  }
  async function salir() {
    if (busy) return
    setBusy(true); setError('')
    try { await logout(); setSession(null); setRegistering(false); setPassword('') }
    catch(e) { setError(e instanceof Error ? e.message : 'No se pudo cerrar sesión.') }
    finally { setBusy(false) }
  }
  if (session) return <Workspace logoutBusy={busy} logoutError={error} user={session} onUserChange={setSession} logout={() => void salir()} />
  return <main className={`login-page ${registering ? "register-mode" : ""}`}><div className="login-shell">
    <section className="login-panel"><div className="login-card">
      <img className="unsa-logo" src="/unsa.jpg" alt="Universidad Nacional de San Agustín de Arequipa" />
      <span className="login-eyebrow">SISTEMA DE PRÉSTAMOS · EPCC</span>
      {registering ? <RegistroCuentaForm onSuccess={user => { setRegistering(false); setSession(user) }} onCancel={() => setRegistering(false)} /> : <>
      <h2>Iniciar sesión</h2><p>Acceso para estudiantes, profesores y administrativos.</p>
      <form onSubmit={submit}>
        <label htmlFor="email">Correo institucional</label><input id="email" type="email" autoComplete="username" placeholder="tu.nombre@epcc.edu.pe" value={email} onChange={event => setEmail(event.target.value)} required />
        <label htmlFor="password">Contraseña</label><div className="login-password"><input id="password" type={visible ? 'text' : 'password'} autoComplete="current-password" placeholder="Ingresa tu contraseña" value={password} onChange={event => setPassword(event.target.value)} required /><button type="button" onClick={() => setVisible(!visible)} aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'} aria-pressed={visible}><span aria-hidden="true">{visible ? '🙉' : '🙈'}</span></button></div>
        {error && <p className="login-error" role="alert">{error}</p>}
        <button className="login-submit" type="submit" disabled={busy}>{busy ? "Verificando cuenta…" : "Iniciar sesión →"}</button>
      </form>
      <button type="button" className="login-register-switch" disabled={busy} onClick={() => { setRegistering(true); setError(''); setPassword('') }}>¿No tienes cuenta? <strong>Crear cuenta</strong></button>
      <details className="login-demo"><summary>Cuentas locales de ejemplo</summary><div><span>Estudiante: ana.ejemplo@unsa.edu.pe</span><span>Profesor: carlos.ejemplo@unsa.edu.pe</span><span>Administrativo: lucia.ejemplo@unsa.edu.pe</span><span>Contraseña de ejemplo: Epcc2026!</span></div></details>
      </>}
      <small className="login-note">Escuela Profesional de Ciencia de la Computación</small>
    </div></section>
    <section className="login-story">
      <span className="story-tag"><i /> EPCC · UNSA</span>
      <div className="story-content"><img className="epcc-logo" src="/epcc.jpg" alt="Computer Science · EPCC - UNSA" /><h1>¡Bienvenido de nuevo!</h1><p>El equipo para tus ideas,<br />a un préstamo de distancia.</p><div className="login-access-types"><span>Estudiantes</span><span>Profesores</span><span>Administrativos</span></div><small>Tu cuenta define las opciones disponibles</small></div>
      <footer>CIENCIA DE LA COMPUTACIÓN <span>AREQUIPA, PERÚ</span></footer>
    </section>
  </div></main>
}
