from enum import Enum


class EstadoNotificacion(Enum):
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    FALLIDA = "fallida"


class EstadoPenalizacion(Enum):
    ACTIVA = "activa"
    PAGADA = "pagada"
    CANCELADA = "cancelada"