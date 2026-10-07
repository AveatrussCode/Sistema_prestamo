from enum import Enum

class EstadoDeDisponibilidad(str,Enum):
    DISPONIBLE = "DISPONIBLE"
    PRESTADO = "PRESTADO"
    RESERVADO = "RESERVADO"
    NO_DISPONIBLE = "NO_DISPONIBLE"
    DADO_DE_BAJA = "DADO_DE_BAJA"

class EstadoFisico(str, Enum):
    BUENO = "BUENO"
    REGULAR = "REGULAR"
    DANHADO = "DANHADO"


