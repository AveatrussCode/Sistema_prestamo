from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from backend.database import Base
from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico


class CategoriaModel(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, default="")


class ObjetoModel(Base):
    __tablename__ = "objetos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(String, default="")
    categoria_id = Column(Integer, nullable=False, index=True)
    estado_disponibilidad = Column(
        SQLEnum(EstadoDeDisponibilidad),
        default=EstadoDeDisponibilidad.DISPONIBLE,
        nullable=False,
    )
    estado_fisico = Column(
        SQLEnum(EstadoFisico),
        default=EstadoFisico.BUENO,
        nullable=False,
    )