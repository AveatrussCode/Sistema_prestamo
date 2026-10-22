import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { crearCategoria, crearObjeto, editarObjeto } from '../../api/objetos'
import type { Categoria, DatosObjeto, Objeto } from '../../api/objetos'

export default function EquipoForm({ equipo, categorias, onClose, onSaved, onCategoria }: {
  equipo: Objeto | null; categorias: Categoria[]; onClose: () => void;
  onSaved: (equipo: Objeto) => void; onCategoria: (categoria: Categoria) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [form, setForm] = useState<DatosObjeto>({ nombre: equipo?.nombre ?? '', descripcion: equipo?.descripcion ?? '', categoria_id: equipo?.categoria_id ?? categorias[0]?.id ?? 0, estado_fisico: equipo?.estado_fisico ?? 'BUENO', estado_disponibilidad: equipo?.estado_disponibilidad ?? 'DISPONIBLE' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [categoryName, setCategoryName] = useState('')
  const [adding, setAdding] = useState(false)
  useEffect(() => { const element = dialog.current; element?.showModal(); return () => element?.close() }, [])
  async function save(e: FormEvent) {
    e.preventDefault(); if (busy) return; setError(''); setBusy(true)
    try {
      const body = { ...form, nombre: form.nombre.trim(), descripcion: form.descripcion.trim() }
      const result = equipo ? await editarObjeto(equipo.id, body) : await crearObjeto(body)
      onSaved(result)
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar el equipo.') }
    finally { setBusy(false) }
  }
  async function addCategory() {
    if (!categoryName.trim() || busy) return
    setBusy(true); setError('')
    try { const category = await crearCategoria(categoryName.trim()); onCategoria(category); setForm({ ...form, categoria_id: category.id }); setCategoryName(''); setAdding(false) }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo crear la categoría.') }
    finally { setBusy(false) }
  }
  return <dialog ref={dialog} className="equipment-dialog" onCancel={e => { e.preventDefault(); if (!busy) onClose() }} aria-labelledby="equipment-title">
    <header><div><span className="section-eyebrow">INVENTARIO · EPCC</span><h2 id="equipment-title">{equipo ? 'Editar equipo' : 'Registrar equipo'}</h2></div><button type="button" aria-label="Cerrar formulario" disabled={busy} onClick={onClose}>×</button></header>
    <p>Completa la información que verá la comunidad en el catálogo.</p>
    {error && <p className="alert alert-error" role="alert">{error}</p>}
    <form onSubmit={save}><fieldset disabled={busy}>
      <label>Nombre del equipo<input autoFocus required minLength={1} maxLength={150} value={form.nombre} onChange={e => setForm({ ...form, nombre: e.target.value })} placeholder="Ej. Laptop Dell Latitude 5420" /></label>
      <label>Descripción<textarea maxLength={2000} rows={3} value={form.descripcion} onChange={e => setForm({ ...form, descripcion: e.target.value })} placeholder="Características, accesorios y detalles del equipo" /></label>
      <label>Categoría<select required value={form.categoria_id || ''} onChange={e => setForm({ ...form, categoria_id: Number(e.target.value) })}><option value="" disabled>Selecciona una categoría</option>{categorias.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></label>
      <button type="button" className="text-button" onClick={() => setAdding(!adding)}>{adding ? 'Cancelar nueva categoría' : '+ Crear categoría'}</button>
      {adding && <div className="new-category"><label>Nueva categoría<input maxLength={100} value={categoryName} onChange={e => setCategoryName(e.target.value)} placeholder="Ej. Monitores" /></label><button type="button" className="btn" disabled={!categoryName.trim()} onClick={() => void addCategory()}>Crear categoría</button></div>}
      <div className="equipment-form-row"><label>Estado físico<select value={form.estado_fisico} onChange={e => setForm({ ...form, estado_fisico: e.target.value as DatosObjeto['estado_fisico'], estado_disponibilidad: e.target.value === 'DANHADO' && form.estado_disponibilidad === 'DISPONIBLE' ? 'NO_DISPONIBLE' : form.estado_disponibilidad })}><option value="BUENO">Bueno</option><option value="REGULAR">Regular</option><option value="DANHADO">Dañado</option></select></label><label>Disponibilidad<select value={form.estado_disponibilidad} onChange={e => setForm({ ...form, estado_disponibilidad: e.target.value as DatosObjeto['estado_disponibilidad'] })}><option value="DISPONIBLE" disabled={form.estado_fisico === 'DANHADO'}>Disponible</option><option value="NO_DISPONIBLE">No disponible</option><option value="RESERVADO">Reservado</option><option value="PRESTADO">Prestado</option><option value="DADO_DE_BAJA">Dado de baja</option></select></label></div>
      {form.estado_fisico === 'DANHADO' && <p className="equipment-help">Los equipos dañados no se ofrecen como disponibles para reservar.</p>}
      {form.estado_disponibilidad === 'DADO_DE_BAJA' && <p className="equipment-help">El equipo quedará oculto del catálogo general. Podrás encontrarlo con el filtro “Dados de baja”.</p>}
    </fieldset><footer><button type="button" className="refresh-button" disabled={busy} onClick={onClose}>Cancelar</button><button className="btn" disabled={busy}>{busy ? 'Guardando…' : equipo ? 'Guardar cambios' : 'Registrar equipo'}</button></footer></form>
  </dialog>
}
