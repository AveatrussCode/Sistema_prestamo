from sqlalchemy import Column, Date, Enum as SQLEnum, ForeignKey, Integer

from backend.database import Base
from backend.prestamos.domain.reserva import EstadoReserva


class ReservaModel(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    objeto_id = Column(Integer, ForeignKey("objetos.id"), nullable=False, index=True)
    fecha_reserva = Column(Date, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(SQLEnum(EstadoReserva), nullable=False, default=EstadoReserva.PENDIENTE)
