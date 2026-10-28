import { useState } from 'react'
import type { FormEvent } from 'react'
import { register } from '../api/auth'
import type { RegistroCuenta } from '../api/auth'
import './registro.css'

export default function RegistroCuentaForm({ onCancel }: { onSuccess?: () => void; onCancel: () => void }) {
  const [form, setForm] = useState<RegistroCuenta>({
    nombre: '', correo: '', codigo: '', tipo: 'Estudiante', password: '',
    especialidad: '', area: '', cargo: '', constancia: null,
  })
  const [confirm, setConfirm] = useState('')
  const [visible, setVisible] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [enviado, setEnviado] = useState(false)

  function setFile(f: File | null) {
    if (!f) { setForm({ ...form, constancia: null }); return }
    if (!f.name.toLowerCase().endsWith('.pdf') || f.size > 5 * 1024 * 1024) {
      setError('Selecciona un PDF de hasta 5 MB.'); return
    }
    setError(''); setForm({ ...form, constancia: f })
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError('')
    if (form.password !== confirm) { setError('Las contraseñas no coinciden.'); return }
    if (form.tipo === 'Estudiante' && !form.constancia) {
      setError('La constancia de matrícula (PDF) es obligatoria.'); return
    }
    setBusy(true)
    try {
      await register(form)
      setEnviado(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo crear tu cuenta.')
    } finally {
      setBusy(false)
    }
  }

  if (enviado) {
    return (
      <div className="registro">
        <h2>Solicitud enviada ✅</h2>
        <p>Tu solicitud está en revisión. Te avisaremos por correo cuando un administrador la revise.</p>
        <button className="login-submit" onClick={onCancel}>Volver al inicio de sesión</button>
      </div>
    )
  }

  return (
    <div className="registro">
      <h2>Crea tu cuenta</h2>
      <p>Únete al sistema de préstamos de la EPCC. Tu solicitud será revisada por un administrador.</p>
      <form onSubmit={submit}>
        <fieldset disabled={busy}>
          <div className="registro-types" role="group" aria-label="Tipo de cuenta">
            {(['Estudiante', 'Profesor', 'Administrativo'] as const).map(t => (
              <button type="button" key={t} className={form.tipo === t ? 'active' : ''}
                aria-pressed={form.tipo === t}
                onClick={() => { setForm({ ...form, tipo: t, constancia: null }); }}>
                {t}
              </button>
            ))}
          </div>

          <label>Nombre completo
            <input autoFocus required minLength={2} maxLength={150} autoComplete="name"
              value={form.nombre} onChange={e => setForm({ ...form, nombre: e.target.value })} />
          </label>
          <div className="registro-row">
            <label>Correo institucional
              <input type="email" required maxLength={200} autoComplete="username"
                placeholder="nombre@unsa.edu.pe"
                value={form.correo} onChange={e => setForm({ ...form, correo: e.target.value })} />
            </label>
            <label>Código institucional
              <input required maxLength={50}
                value={form.codigo} onChange={e => setForm({ ...form, codigo: e.target.value })} />
            </label>
          </div>

          {form.tipo === 'Profesor' && (
            <label>Especialidad
              <input maxLength={150} placeholder="Ej. Ingeniería de Software"
                value={form.especialidad} onChange={e => setForm({ ...form, especialidad: e.target.value })} />
            </label>
          )}
          {form.tipo === 'Administrativo' && (
            <div className="registro-row">
              <label>Área
                <input required maxLength={150} placeholder="Ej. Dirección de Escuela"
                  value={form.area} onChange={e => setForm({ ...form, area: e.target.value })} />
              </label>
              <label>Cargo
                <input required maxLength={150} placeholder="Ej. Secretaria Académica"
                  value={form.cargo} onChange={e => setForm({ ...form, cargo: e.target.value })} />
              </label>
            </div>
          )}

          <div className="registro-row">
            <label>Contraseña
              <div className="login-password">
                <input required minLength={8} maxLength={128} autoComplete="new-password"
                  type={visible ? 'text' : 'password'} placeholder="Mínimo 8 caracteres"
                  value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
                <button type="button" aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  aria-pressed={visible} onClick={() => setVisible(!visible)}>
                  <span aria-hidden="true">{visible ? '🙉' : '🙈'}</span>
                </button>
              </div>
            </label>
            <label>Confirma tu contraseña
              <input required minLength={8} maxLength={128} autoComplete="new-password"
                type={visible ? 'text' : 'password'}
                value={confirm} onChange={e => setConfirm(e.target.value)} />
            </label>
          </div>
          <small>Escuela Profesional de Ciencia de la Computación · UNSA</small>
        </fieldset>

        {form.tipo === 'Estudiante' && (
          <label className="registro-pdf">
            Constancia de matrícula (PDF) *
            <input disabled={busy} type="file" accept=".pdf,application/pdf"
              onChange={e => setFile(e.target.files?.[0] ?? null)} />
            <small>{form.constancia ? form.constancia.name : 'Obligatoria. Máximo 5 MB.'}</small>
          </label>
        )}

        {error && <p className="login-error" role="alert">{error}</p>}
        <button className="login-submit" disabled={busy}>
          {busy ? 'Enviando solicitud…' : 'Enviar solicitud →'}
        </button>
      </form>
      <button type="button" className="registro-back" disabled={busy} onClick={onCancel}>
        ¿Ya tienes cuenta? Inicia sesión
      </button>
      <small className="registro-admin">Todas las cuentas pasan por revisión del administrador.</small>
    </div>
  )
}