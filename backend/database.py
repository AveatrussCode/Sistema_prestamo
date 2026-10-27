import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar variables de entorno desde .env
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# Leer la URL de conexión (fallback a SQLite si no hay .env)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sistema_prestamo.db")
database_url = make_url(SQLALCHEMY_DATABASE_URL)
if database_url.drivername in ("postgres", "postgresql"):
    database_url = database_url.set(drivername="postgresql+psycopg")
if database_url.get_backend_name() == "sqlite" and database_url.database not in (None, "", ":memory:"):
    database_path = Path(database_url.database)
    if not database_path.is_absolute():
        database_url = database_url.set(database=str((PROJECT_ROOT / database_path).resolve()))

# El connect_args solo es necesario para SQLite
if database_url.get_backend_name() == "sqlite":
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 15})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
