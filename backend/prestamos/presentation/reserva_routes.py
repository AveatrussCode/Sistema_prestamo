from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.prestamos.application.reserva_service import ReservaService
from backend.prestamos.domain.reserva import EstadoReserva, Reserva
from backend.prestamos.infrastructure.sql_reserva_repository import SqlReservaRepository
from backend.recursos.infrastructure.sql_objeto_repository import SqlObjetoRepository
from backend.usuarios.infraestructure.usuario_repository import UsuarioRepository

router = APIRouter(prefix="/reservas", tags=["Reservas"])


# ---------- 1) Esquema de entrada: qué JSON acepta el endpoint ----------

class ReservaCreate(BaseModel):
    usuario_id: int
    objeto_id: int
    fecha_inicio: date    # "2026-11-03"
    fecha_fin: date


# ---------- 2) Armado del servicio (inyección de dependencias) ----------

def get_reserva_service(db: Session = Depends(get_db)) -> ReservaService:
    return ReservaService(SqlReservaRepository(db), SqlObjetoRepository(db), UsuarioRepository(db))


# ---------- 3) Salida: entidad de dominio -> JSON ----------

def _a_dict(r: Reserva) -> dict:
    return {
        "id": r.id_reserva,
        "usuario_id": r.usuario_id,
        "objeto_id": r.objeto_id,
        "fecha_reserva": r.fecha_reserva.isoformat(),
        "fecha_inicio": r.fecha_inicio.isoformat(),
        "fecha_fin": r.fecha_fin.isoformat(),
        "estado": r.estado.value,
    }


# ---------- 4) Endpoints: delgados, solo traducen HTTP <-> servicio ----------

@router.post("/", status_code=201)
def crear_reserva(datos: ReservaCreate, servicio: ReservaService = Depends(get_reserva_service)):
    """RF17 - Reserva de objetos."""
    return _a_dict(servicio.crear(datos.usuario_id, datos.objeto_id,
                                  datos.fecha_inicio, datos.fecha_fin))


@router.get("/")
def listar_reservas(
    usuario_id: int | None = Query(None),
    objeto_id: int | None = Query(None),
    estado: EstadoReserva | None = Query(None),
    servicio: ReservaService = Depends(get_reserva_service),
):
    """RF18 - Consulta de reservas (con filtros opcionales)."""
    return [_a_dict(r) for r in servicio.listar(usuario_id, objeto_id, estado)]


@router.post("/procesar-vencidas")
def procesar_vencidas(servicio: ReservaService = Depends(get_reserva_service)):
    """Marca como VENCIDAS las reservas activas cuya fecha de fin ya pasó."""
    return [_a_dict(r) for r in servicio.marcar_vencidas()]


@router.get("/{id_reserva}")
def obtener_reserva(id_reserva: int, servicio: ReservaService = Depends(get_reserva_service)):
    return _a_dict(servicio.obtener(id_reserva))


@router.post("/{id_reserva}/confirmar")
def confirmar_reserva(id_reserva: int, servicio: ReservaService = Depends(get_reserva_service)):
    return _a_dict(servicio.confirmar(id_reserva))


@router.post("/{id_reserva}/cancelar")
def cancelar_reserva(id_reserva: int, servicio: ReservaService = Depends(get_reserva_service)):
    """RF18 - Cancelación de reservas."""
    return _a_dict(servicio.cancelar(id_reserva))


@router.post("/{id_reserva}/finalizar")
def finalizar_reserva(id_reserva: int, servicio: ReservaService = Depends(get_reserva_service)):
    return _a_dict(servicio.finalizar(id_reserva))
