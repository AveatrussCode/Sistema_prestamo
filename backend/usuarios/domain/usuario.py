from abc import ABC
from enum import Enum


class EstadoUsuario(Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"


class Usuario(ABC):
    def __init__(self, id_usuario: int, nombre: str, correo: str, codigo: str,
                 credibilidad: float, estado: EstadoUsuario, rol_id: int = None):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.correo_institucional = correo
        self.codigo_institucional = codigo
        self.credibilidad = credibilidad
        self.estado = estado
        self.rol_id = rol_id

    def actualizar_perfil(self, nuevo_nombre: str, nuevo_correo: str):
        self.nombre = nuevo_nombre
        self.correo_institucional = nuevo_correo

    def activar(self):
        self.estado = EstadoUsuario.ACTIVO

    def desactivar(self):
        self.estado = EstadoUsuario.INACTIVO

    def suspender(self):
        self.estado = EstadoUsuario.SUSPENDIDO


class Estudiante(Usuario):
    def __init__(self, id_usuario, nombre, correo, codigo, credibilidad, estado,
                 carrera: str, matricula: str, rol_id: int = None):
        super().__init__(id_usuario, nombre, correo, codigo, credibilidad, estado, rol_id)
        self.carrera = carrera
        self.matricula = matricula


class Profesor(Usuario):
    def __init__(self, id_usuario, nombre, correo, codigo, credibilidad, estado,
                 departamento: str, especialidad: str, rol_id: int = None):
        super().__init__(id_usuario, nombre, correo, codigo, credibilidad, estado, rol_id)
        self.departamento = departamento
        self.especialidad = especialidad


class Administrativo(Usuario):
    def __init__(self, id_usuario, nombre, correo, codigo, credibilidad, estado,
                 area: str, cargo: str, rol_id: int = None):
        super().__init__(id_usuario, nombre, correo, codigo, credibilidad, estado, rol_id)
        self.area = area
        self.cargo = cargo