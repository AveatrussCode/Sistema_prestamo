import { useCallback, useEffect, useMemo, useState } from 'react'
import { listarCategorias, listarObjetos, imagenUrl } from '../../api/objetos'
import type { Categoria, EstadoDisponibilidad, Objeto } from '../../api/objetos'
import EquipoForm from './EquipoForm'
import './catalogo.css'

const etiquetas: Record<EstadoDisponibilidad, string> = { DISPONIBLE: 'Disponible', PRESTADO: 'Prestado', RESERVADO: 'Reservado', NO_DISPONIBLE: 'No disponible', DADO_DE_BAJA: 'Dado de baja' }
const fisico = { BUENO: 'Buen estado', REGULAR: 'Estado regular', DANHADO: 'Dañado' }
const normalize = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
const reservable = (o: Objeto) => o.estado_disponibilidad === 'DISPONIBLE' && o.estado_fisico !== 'DANHADO'

function EquipoIcon({ categoria }: { categoria: string }) {
  const text = normalize(categoria)
  const path = text.includes('laptop') ? 'M5 4h14v12H5ZM5 16l-3 4h20l-3-4M9 19h6'
    : text.includes('proyector') ? 'M3 7h18v11H3ZM7 11h2M7 14h2M16 15a2 2 0 1 0 0-4 2 2 0 0 0 0 4M6 18v2M18 18v2'
    : text.includes('camara') ? 'M4 5h16v12H4ZM9 21h6M12 17v4M12 14a3 3 0 1 0 0-6 3 3 0 0 0 0 6'
    : text.includes('electron') ? 'M7 7h10v10H7ZM10 10h4v4h-4M9 3v4M15 3v4M9 17v4M15 17v4M3 9h4M3 15h4M17 9h4M17 15h4'
    : 'M3 7l9-4 9 4v11l-9 4-9-4ZM3 7l9 4 9-4M12 11v11'
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={path} /></svg>
}

export default function CatalogoPage({ onReservar, administrador = false }: { onReservar: (id: number) => void; administrador?: boolean }) {
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Objeto | null>(null)
  const [notice, setNotice] = useState('')
  const [objetos, setObjetos] = useState<Objeto[]>([])
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [categoriaId, setCategoriaId] = useState('')
  const [estado, setEstado] = useState('')
  const [orden, setOrden] = useState('nombre')

  const cargar = useCallback(() => {
    return Promise.all([listarObjetos(), administrador ? listarObjetos({ estado: 'DADO_DE_BAJA' }) : Promise.resolve([]), listarCategorias()])
      .then(([activos, bajas, cats]) => { setObjetos([...activos, ...bajas]); setCategorias(cats) })
      .catch((e: unknown) => { setError(e instanceof Error ? e.message : 'No se pudo cargar el catálogo.') })
      .finally(() => setCargando(false))
  }, [administrador])
  
  async function refresh() { setCargando(true); setError(''); await cargar() }
  useEffect(() => { void cargar() }, [cargar])
  
  const nombreCategoria = (id: number) => categorias.find(c => c.id === id)?.nombre ?? 'Sin categoría'
  
  const visibles = useMemo(() => {
    const query = normalize(busqueda.trim())
    const result = objetos.filter(o => (estado ? o.estado_disponibilidad === estado : o.estado_disponibilidad !== 'DADO_DE_BAJA') && (!categoriaId || o.categoria_id === Number(categoriaId)) && (!query || normalize(`${o.nombre} ${o.descripcion} ${categorias.find(c => c.id === o.categoria_id)?.nombre ?? ''}`).includes(query)))
    return result.sort((a, b) => orden === 'recientes' ? b.id - a.id : orden === 'disponibilidad' ? Number(reservable(b)) - Number(reservable(a)) || a.nombre.localeCompare(b.nombre, 'es') : a.nombre.localeCompare(b.nombre, 'es'))
  }, [objetos, categorias, busqueda, categoriaId, estado, orden])
  
  const filtered = Boolean(busqueda || categoriaId || estado)
  function clear() { setBusqueda(''); setCategoriaId(''); setEstado('') }

  return <div className="page-catalogo">
    <header className="topbar">
      <div>
        <span className="section-eyebrow">RECURSOS PARA TUS IDEAS</span>
        <h1>{administrador ? 'Catálogo e inventario' : 'Explora. Elige. Crea.'}</h1>
        <p>{administrador ? 'Cada equipo, su estado y sus posibilidades. Todo en un solo lugar.' : 'Encuentra el equipo que necesitas para tu próximo proyecto.'}</p>
      </div>
      {administrador && <button className="primary-button" onClick={() => { setEditing(null); setNotice(''); setFormOpen(true) }}>+ Registrar equipo</button>}
    </header>
    
    <section className="catalog-summary" aria-label="Disponibilidad del catálogo">
      <span><b>{cargando || error ? '—' : objetos.filter(o => o.estado_disponibilidad !== 'DADO_DE_BAJA').length}</b> equipos en catálogo</span>
      <span><i /> <b>{cargando || error ? '—' : objetos.filter(reservable).length}</b> disponibles para reservar</span>
    </section>
    
    {notice && <p className="inventory-success" role="status">{notice}</p>}
    
    <section className="catalog-search-panel" aria-label="Filtros de equipos">
      <div className="catalog-search-row">
        <label className="catalog-search">
          <span className="sr-only">Buscar equipos</span>
          <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><circle cx="10" cy="10" r="6" /><path d="m15 15 5 5" /></svg>
          <input type="search" placeholder="Busca por nombre, descripción o categoría…" value={busqueda} onChange={e => setBusqueda(e.target.value)} />
        </label>
        <label className="catalog-status-filter">
          <span className="sr-only">Filtrar disponibilidad</span>
          <select value={estado} onChange={e => setEstado(e.target.value)}>
            <option value="">{administrador ? 'Todos los activos' : 'Cualquier disponibilidad'}</option>
            {Object.entries(etiquetas).filter(([value]) => administrador || value !== 'DADO_DE_BAJA').map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
      </div>
      <div className="category-chips" role="group" aria-label="Filtrar por categoría">
        <button aria-pressed={!categoriaId} onClick={() => setCategoriaId('')}>Todos los equipos</button>
        {categorias.map(c => <button key={c.id} aria-pressed={categoriaId === String(c.id)} onClick={() => setCategoriaId(String(c.id))}>{c.nombre}</button>)}
      </div>
    </section>
    
    <div className="catalog-results-bar">
      <p role="status" aria-live="polite">
        {cargando ? 'Consultando equipos…' : error ? 'Catálogo no disponible' : <><strong>{visibles.length}</strong> {visibles.length === 1 ? 'equipo encontrado' : 'equipos encontrados'}</>}
        {filtered && <button className="text-button" onClick={clear}>Limpiar filtros ×</button>}
      </p>
      <label>Ordenar por
        <select value={orden} onChange={e => setOrden(e.target.value)}>
          <option value="nombre">Nombre: A–Z</option>
          <option value="disponibilidad">Disponibles primero</option>
          <option value="recientes">Más recientes</option>
        </select>
      </label>
    </div>
    
    {error ? (
      <div className="catalog-empty" role="alert"><h2>No pudimos cargar los equipos</h2><p>{error}</p><button className="primary-button" onClick={() => void refresh()}>Reintentar</button></div>
    ) : cargando ? (
      <div className="catalogo-grid" aria-busy="true" aria-label="Cargando catálogo">{[0, 1, 2, 3, 4, 5].map(i => <div className="catalog-skeleton" key={i} aria-hidden="true"><div /><span /><span /></div>)}</div>
    ) : !visibles.length ? (
      <div className="catalog-empty">
        <span className="empty-icon"><EquipoIcon categoria="" /></span>
        <h2>{filtered ? 'No encontramos ese equipo' : 'Pronto habrá más ideas por crear'}</h2>
        <p>{filtered ? 'Prueba con otro nombre o cambia los filtros para explorar más opciones.' : 'Todavía no hay equipos registrados en el catálogo.'}</p>
        {filtered ? <button className="primary-button" onClick={clear}>Ver todos los equipos</button> : administrador && <button className="primary-button" onClick={() => { setEditing(null); setFormOpen(true) }}>Registrar primer equipo</button>}
      </div>
    ) : (
      <div className="catalogo-grid">
        {visibles.map(o => {
          const category = nombreCategoria(o.categoria_id)
          const canReserve = reservable(o)
          return (
            <article className="objeto-card" key={o.id}>
              {/* --- BLOQUE VISUAL MODIFICADO --- */}
              <div className={`equipment-visual visual-${o.imagen_url ? 'img' : normalize(category).includes('laptop') ? 'laptop' : normalize(category).includes('electron') ? 'electronics' : normalize(category).includes('camara') ? 'camera' : 'other'}`}>
                <span className={`equipment-status status-${o.estado_disponibilidad.toLowerCase()}`}><i />{etiquetas[o.estado_disponibilidad]}</span>
                {o.imagen_url ? (
                  <img src={imagenUrl(o.id)} alt={o.nombre} className="equipment-real-img" />
                ) : (
                  <EquipoIcon categoria={category} />
                )}
                <small>EPCC · EQUIPO #{String(o.id).padStart(3, '0')}</small>
              </div>
              
              <div className="equipment-card-body">
                <span className="categoria-tag">{category}</span>
                <h2>{o.nombre}</h2>
                <p className="equipment-description">{o.descripcion || 'Consulta los detalles del equipo con el responsable de recursos.'}</p>
                <div className={`physical-condition condition-${o.estado_fisico.toLowerCase()}`}>
                  <span aria-hidden="true">{o.estado_fisico === 'BUENO' ? '✓' : '!'}</span>{fisico[o.estado_fisico]}
                </div>
                <div className="equipment-card-actions">
                  <button className="btn-reservar" disabled={!canReserve} onClick={() => onReservar(o.id)}>
                    {canReserve ? 'Reservar equipo' : 'No disponible para reservar'}
                    {canReserve && <span aria-hidden="true">↗</span>}
                  </button>
                  {administrador && <button className="inventory-edit" aria-label={`Editar ${o.nombre}`} onClick={() => { setEditing(o); setNotice(''); setFormOpen(true) }}>Editar equipo <span aria-hidden="true">→</span></button>}
                </div>
              </div>
            </article>
          )
        })}
      </div>
    )}
    
    {administrador && formOpen && <EquipoForm equipo={editing} categorias={categorias} onClose={() => setFormOpen(false)} onCategoria={c => setCategorias(current => [...current, c])} onSaved={o => { setFormOpen(false); setNotice(`${o.nombre}: ${editing ? 'cambios guardados' : 'equipo registrado'}.`); void refresh() }} />}
  </div>
}