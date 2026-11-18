"""Rutas del reporte de usuario. Archivo de la Persona 2: aquí agrega sus rutas GET (quedan bajo /reportes/...)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.control.application.reporte_usuario_service import ReporteUsuarioService
from backend.control.infraestructure.sql_usuario_reporte_repository import SqlUsuarioReporteRepository
from backend.database import get_db
from backend.usuarios.presentation.auth_routes import usuario_actual

router = APIRouter()


# Aquí se "cablea": se elige qué repositorio concreto (SQL) usa el servicio.
def get_reporte_usuario_service(db: Session = Depends(get_db)) -> ReporteUsuarioService:
    return ReporteUsuarioService(SqlUsuarioReporteRepository(db))


@router.get("/usuario/{id_usuario}")
def reporte_de_usuario(
    id_usuario: int,
    actor=Depends(usuario_actual),
    servicio: ReporteUsuarioService = Depends(get_reporte_usuario_service),
):
    es_admin = bool(actor.rol and actor.rol.nombre == "ADMIN")
    if actor.id != id_usuario and not es_admin:
        raise HTTPException(403, "Solo puedes ver tu propio reporte.")
    return servicio.generar(id_usuario)
