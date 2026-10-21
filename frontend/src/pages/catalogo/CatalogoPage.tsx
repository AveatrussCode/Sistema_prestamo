import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { listarCategorias, listarObjetos } from "../../api/objetos";
import type { Categoria, EstadoDisponibilidad, Objeto } from "../../api/objetos";
import "./catalogo.css";

const mensajeDe = (e: unknown) => (e instanceof Error ? e.message : "Ocurrió un error");

const colorEstado: Record<EstadoDisponibilidad, string> = {
  DISPONIBLE: "available",
  PRESTADO: "borrowed",
  RESERVADO: "reserved",
  NO_DISPONIBLE: "borrowed",
  DADO_DE_BAJA: "borrowed",
};

const etiquetaEstado: Record<EstadoDisponibilidad, string> = {
  DISPONIBLE: "Disponible",
  PRESTADO: "Prestado",
  RESERVADO: "Reservado",
  NO_DISPONIBLE: "No disponible",
  DADO_DE_BAJA: "Dado de baja",
};

const etiquetaFisico = { BUENO: "Buen estado", REGULAR: "Regular", DANHADO: "Dañado" };

export default function CatalogoPage() {
  const [objetos, setObjetos] = useState<Objeto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [busqueda, setBusqueda] = useState("");
  const [categoriaId, setCategoriaId] = useState("");
  const [soloDisponibles, setSoloDisponibles] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [o, c] = await Promise.all([
        listarObjetos({
          busqueda: busqueda || undefined,
          categoria_id: categoriaId ? Number(categoriaId) : undefined,
          solo_disponibles: soloDisponibles || undefined,
        }),
        listarCategorias(),
      ]);
      setObjetos(o);
      setCategorias(c);
    } catch (e) {
      setError(mensajeDe(e));
    } finally {
      setCargando(false);
    }
  }, [busqueda, categoriaId, soloDisponibles]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  function buscar(e: FormEvent) {
    e.preventDefault();
    void cargar();
  }

  const nombreCategoria = (id: number) =>
    categorias.find((c) => c.id === id)?.nombre ?? `Categoría #${id}`;

  return (
    <div className="page-catalogo">
      <header className="topbar">
        <div>
          <h1>Catálogo de objetos</h1>
          <p>Explora lo que puedes reservar</p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="panel">
        <form className="catalogo-filtros" onSubmit={buscar}>
          <label className="field">
            Buscar
            <input
              type="text"
              placeholder="Nombre o descripción..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </label>

          <label className="field">
            Categoría
            <select value={categoriaId} onChange={(e) => setCategoriaId(e.target.value)}>
              <option value="">Todas</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </label>

          <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={soloDisponibles}
              onChange={(e) => setSoloDisponibles(e.target.checked)}
            />
            Solo disponibles
          </label>

          <button className="btn" type="submit">Buscar</button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Objetos</h2>
            <p>{objetos.length} resultados</p>
          </div>
        </div>

        {cargando && <p className="hint">Cargando...</p>}
        {!cargando && objetos.length === 0 && (
          <p className="hint">No hay objetos que coincidan con los filtros.</p>
        )}

        <div className="catalogo-grid">
          {objetos.map((o) => (
            <article className="objeto-card" key={o.id}>
              <span className="categoria-tag">{nombreCategoria(o.categoria_id)}</span>
              <h3>{o.nombre}</h3>
              <p>{o.descripcion || "Sin descripción."}</p>

              <div className="footer">
                <span className={`status ${colorEstado[o.estado_disponibilidad]}`}>
                  {etiquetaEstado[o.estado_disponibilidad]}
                </span>
                <button
                  className="btn-reservar"
                  disabled={o.estado_disponibilidad !== "DISPONIBLE"}
                  onClick={() => alert(`Reservar "${o.nombre}"`)}
                >
                  Reservar
                </button>
              </div>

              <span style={{ fontSize: 11, color: "#9ca3af" }}>
                Estado físico: {etiquetaFisico[o.estado_fisico]}
              </span>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}