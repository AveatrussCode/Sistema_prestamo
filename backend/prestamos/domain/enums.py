
from enum import Enum

class EstadoReserva(str, Enum):
    PENDIENTE = "PENDIENTE"      # recién creada
    CONFIRMADA = "CONFIRMADA"    # aprobada por un administrativo
    FINALIZADA = "FINALIZADA"    # ya se usó (se convirtió en préstamo / terminó)
    CANCELADA = "CANCELADA"
    VENCIDA = "VENCIDA"          # pasó su fecha_fin sin finalizarse


class EstadoPrestamo(str, Enum):
    ACTIVO = "activo"
    DEVUELTO = "devuelto"
    CANCELADO = "cancelado"


class EstadoDeSolicitudPrestamo(str, Enum):
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    CANCELADO = "cancelado"


class EstadoFisico(str, Enum):
    BUENO = "Bueno"
    REGULAR = "Regular"
    DANADO = "Dañado"
