

from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico
class Objeto :

    nombre: str
    descripcion:str
    categoria_id: int
    estado_disponibilidad: str
    estado_fisico: str

    #funciones
    def __init__(self,nombre: str,descripcion: str,categoria_id: int):
        self.nombre = nombre
        self.descripcion = descripcion
        self.categoria_id = categoria_id
        self.estado_disponibilidad = EstadoDeDisponibilidad.DISPONIBLE
        self.estado_fisico = EstadoFisico.BUENO

    def esta_disponible(self) -> bool:
        return self.estado_disponibilidad == EstadoDeDisponibilidad.DISPONIBLE

    def esta_operativo(self) -> bool:
        return self.estado_fisico != EstadoFisico.DANHADO
    
    def marcar_disponible(self)-> bool:
        self.estado_disponibilidad = EstadoDeDisponibilidad.DISPONIBLE
        return True

    def marcar_prestado(self)-> bool:
        self.estado_disponibilidad = EstadoDeDisponibilidad.PRESTADO
        return True
    
    def marcar_reservado(self) -> bool:
        self.estado_disponibilidad = EstadoDeDisponibilidad.RESERVADO
        return True
    
    def marcar_no_disponible(self) -> bool:
        self.estado_disponibilidad = EstadoDeDisponibilidad.NO_DISPONIBLE
        return True

    def dar_de_baja(self) -> bool:
        self.estado_disponibilidad = EstadoDeDisponibilidad.DADO_DE_BAJA


















