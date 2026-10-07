from sqlalchemy.orm import Session
from backend.usuarios.domain.usuario import Estudiante, Profesor, Administrativo, Usuario
from backend.usuarios.infraestructure.models import (
    UsuarioModel,
    EstudianteModel,
    ProfesorModel,
    AdministrativoModel,
    RolModel
)


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, usuario_domain: Usuario):
        """Guarda un usuario en la base de datos según su tipo."""
        if isinstance(usuario_domain, Estudiante):
            db_usuario = EstudianteModel(
                nombre=usuario_domain.nombre,
                correo_institucional=usuario_domain.correo_institucional,
                codigo_institucional=usuario_domain.codigo_institucional,
                credibilidad=usuario_domain.credibilidad,
                estado=usuario_domain.estado,
                carrera=usuario_domain.carrera,
                matricula=usuario_domain.matricula,
                rol_id=usuario_domain.rol_id,
                tipo="estudiante"
            )
        elif isinstance(usuario_domain, Profesor):
            db_usuario = ProfesorModel(
                nombre=usuario_domain.nombre,
                correo_institucional=usuario_domain.correo_institucional,
                codigo_institucional=usuario_domain.codigo_institucional,
                credibilidad=usuario_domain.credibilidad,
                estado=usuario_domain.estado,
                departamento=usuario_domain.departamento,
                especialidad=usuario_domain.especialidad,
                rol_id=usuario_domain.rol_id,
                tipo="profesor"
            )
        elif isinstance(usuario_domain, Administrativo):
            db_usuario = AdministrativoModel(
                nombre=usuario_domain.nombre,
                correo_institucional=usuario_domain.correo_institucional,
                codigo_institucional=usuario_domain.codigo_institucional,
                credibilidad=usuario_domain.credibilidad,
                estado=usuario_domain.estado,
                area=usuario_domain.area,
                cargo=usuario_domain.cargo,
                rol_id=usuario_domain.rol_id,
                tipo="administrativo"
            )
        else:
            raise ValueError("Tipo de usuario no soportado por el repositorio")

        self.db.add(db_usuario)
        self.db.commit()
        self.db.refresh(db_usuario)
        return db_usuario

    def obtener_por_correo(self, correo: str):
        return self.db.query(UsuarioModel).filter(
            UsuarioModel.correo_institucional == correo
        ).first()

    def obtener_por_id(self, id_usuario: int):
        return self.db.query(UsuarioModel).filter(UsuarioModel.id == id_usuario).first()

    def listar_todos(self):
        return self.db.query(UsuarioModel).all()

    def asignar_rol(self, id_usuario: int, id_rol: int):
        """Asigna un rol a un usuario existente."""
        usuario = self.obtener_por_id(id_usuario)
        if not usuario:
            raise ValueError(f"Usuario con id {id_usuario} no encontrado")

        rol = self.db.query(RolModel).filter(RolModel.id == id_rol).first()
        if not rol:
            raise ValueError(f"Rol con id {id_rol} no encontrado")

        usuario.rol_id = id_rol
        self.db.commit()
        self.db.refresh(usuario)
        return usuario


class RolRepository:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, nombre: str, permisos: str, nivel: str):
        rol = RolModel(nombre=nombre, permisos=permisos, nivel=nivel)
        self.db.add(rol)
        self.db.commit()
        self.db.refresh(rol)
        return rol

    def obtener_por_nombre(self, nombre: str):
        return self.db.query(RolModel).filter(RolModel.nombre == nombre).first()

    def obtener_por_id(self, id_rol: int):
        return self.db.query(RolModel).filter(RolModel.id == id_rol).first()

    def listar_todos(self):
        return self.db.query(RolModel).all()