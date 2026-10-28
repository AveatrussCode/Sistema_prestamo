from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum, DateTime, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.usuarios.domain.usuario import EstadoUsuario


class RolModel(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    permisos = Column(String, default="")
    nivel = Column(String, nullable=False)


class UsuarioModel(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo_institucional = Column(String, unique=True, index=True, nullable=False)
    codigo_institucional = Column(String, unique=True, nullable=False)
    credibilidad = Column(Float, default=100.0)
    estado = Column(SQLEnum(EstadoUsuario), default=EstadoUsuario.ACTIVO)

    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    rol = relationship("RolModel", lazy="joined")

    tipo = Column(String(50))

    carrera = Column(String, nullable=True)
    matricula = Column(String, nullable=True)
    departamento = Column(String, nullable=True)
    especialidad = Column(String, nullable=True)
    area = Column(String, nullable=True)
    cargo = Column(String, nullable=True)

    # ---- NUEVOS CAMPOS PARA EL FLUJO DE APROBACIÓN ----
    motivo_rechazo = Column(String, nullable=True)
    fecha_solicitud = Column(DateTime, nullable=True)
    revisado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_revision = Column(DateTime, nullable=True)
    verificado_externo = Column(Boolean, default=False, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'usuario',
        'polymorphic_on': tipo
    }


class EstudianteModel(UsuarioModel):
    __mapper_args__ = {'polymorphic_identity': 'estudiante'}


class ProfesorModel(UsuarioModel):
    __mapper_args__ = {'polymorphic_identity': 'profesor'}


class AdministrativoModel(UsuarioModel):
    __mapper_args__ = {'polymorphic_identity': 'administrativo'}