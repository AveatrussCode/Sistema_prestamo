from sqlalchemy import Column, Date, Integer, Enum as SQLEnum

from backend.database import Base
from backend.prestamos.domain.reserva import EstadoReserva


class ReservaModel(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    objeto_id = Column(Integer, nullable=False, index=True)
    fecha_reserva = Column(Date, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(
        SQLEnum(EstadoReserva),
        nullable=False,
        default=EstadoReserva.PENDIENTE,
    )