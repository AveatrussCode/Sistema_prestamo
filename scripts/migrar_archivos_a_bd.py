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
    
    # 1. Modificar tabla 'objetos'
    cols_objetos = {c["name"] for c in insp.get_columns("objetos")}
    if "imagen_blob" not in cols_objetos:
        print("➕ Añadiendo columna 'imagen_blob' a 'objetos'...")
        # En Postgres, BYTEA es el equivalente a LargeBinary
        conn.execute(text("ALTER TABLE objetos ADD COLUMN imagen_blob BYTEA"))
        # Opcional: eliminar la columna vieja
        if "imagen_path" in cols_objetos:
            conn.execute(text("ALTER TABLE objetos DROP COLUMN imagen_path"))
    
    # 2. Modificar tabla 'cuentas' (para el PDF de matrícula)
    cols_cuentas = {c["name"] for c in insp.get_columns("cuentas")}
    if "constancia_blob" not in cols_cuentas:
        print("➕ Añadiendo columna 'constancia_blob' a 'cuentas'...")
        conn.execute(text("ALTER TABLE cuentas ADD COLUMN constancia_blob BYTEA"))
        conn.execute(text("ALTER TABLE cuentas ADD COLUMN constancia_nombre VARCHAR"))
        
    conn.commit()
    print("✅ Migración completada. Ya puedes borrar la carpeta 'uploads' manualmente.")