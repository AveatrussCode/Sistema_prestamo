import os
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

with engine.connect() as conn:
    insp = inspect(conn)
    existentes = {c["name"] for c in insp.get_columns("objetos")}

    if "imagen_path" not in existentes:
        print("➕ Añadiendo columna 'imagen_path' a la tabla 'objetos'...")
        conn.execute(text("ALTER TABLE objetos ADD COLUMN imagen_path VARCHAR"))
        conn.commit()
        print("✅ Columna añadida.")
    else:
        print("ℹ️ La columna 'imagen_path' ya existe. Omitiendo.")