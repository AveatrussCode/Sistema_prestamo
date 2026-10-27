
from enum import Enum

class EstadoPrestamo(str, Enum):
    ACTIVO = "activo"
    DEVUELTO = "devuelto"
    CANCELADO = "cancelado"


class EstadoDeSolicitudPrestamo(str, Enum):
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    CANCELADO = "cancelado"


class TipoEventoPrestamo(str, Enum):
    """Qué pasó con el préstamo. Corresponde a las acciones de Prestamo en el diagrama."""
    INICIADO = "INICIADO"       # Prestamo.iniciar()
    RENOVADO = "RENOVADO"       # Prestamo.renovar()
    DEVUELTO = "DEVUELTO"       # Prestamo.registrarDevolucion()
    CANCELADO = "CANCELADO"     # Prestamo.cancelar()
    VENCIDO = "VENCIDO"         # Prestamo.estaVencido() pasó a verdadero
