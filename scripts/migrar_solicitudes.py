"""Añade las columnas y valores ENUM necesarios para el flujo de aprobación.

Uso:  python -X utf8 scripts/migrar_solicitudes.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import make_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

URL = os.getenv("DATABASE_URL", "sqlite:///./sistema_prestamo.db")
url = make_url(URL)
if url.drivername in ("postgres", "postgresql"):
    url = url.set(drivername="postgresql+psycopg")

engine = create_engine(url)

COLUMNAS_NUEVAS = [
    ("motivo_rechazo", "VARCHAR"),
    ("fecha_solicitud", "TIMESTAMP"),
    ("revisado_por_id", "INTEGER REFERENCES usuarios(id)"),
    ("fecha_revision", "TIMESTAMP"),
    ("verificado_externo", "BOOLEAN DEFAULT FALSE NOT NULL"),
]

with engine.connect() as conn:
    dialecto = conn.dialect.name
    print(f"🔌 Dialecto: {dialecto}")

    # 1) Añadir valor al ENUM (solo Postgres, fuera de transacción)
    if dialecto == "postgresql":
        print("🔧 Añadiendo 'PENDIENTE_APROBACION' al tipo estadousuario…")
        # Usamos autocommit para que ALTER TYPE no falle
        conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            conn.execute(text("ALTER TYPE estadousuario ADD VALUE IF NOT EXISTS 'PENDIENTE_APROBACION'"))
            print("✅ ENUM actualizado.")
        except Exception as e:
            print(f"⚠️  No se pudo actualizar el ENUM (¿ya existía?): {e}")

    # 2) Añadir columnas si no existen
    insp = inspect(conn)
    existentes = {c["name"] for c in insp.get_columns("usuarios")}

    for nombre, tipo in COLUMNAS_NUEVAS:
        if nombre in existentes:
            print(f"ℹ️  Columna '{nombre}' ya existe. Omitiendo.")
            continue
        sql = f"ALTER TABLE usuarios ADD COLUMN {nombre} {tipo}"
        print(f"➕ {sql}")
        conn.execute(text(sql))

    # 3) Rellenar fecha_solicitud en los usuarios existentes (opcional)
    conn.execute(text(
        "UPDATE usuarios SET fecha_solicitud = CURRENT_TIMESTAMP "
        "WHERE fecha_solicitud IS NULL"
    ))
    conn.commit()

print("\n✅ Migración completada.")