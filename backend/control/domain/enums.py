from enum import Enum


class EstadoNotificacion(Enum):
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    FALLIDA = "fallida"


class EstadoPenalizacion(Enum):
    ACTIVA = "activa"
    PAGADA = "pagada"
    CANCELADA = "cancelada"


class EstadoNotificacion(Enum):
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    FALLIDA = "fallida"


class EstadoMovimiento(Enum):
    APLICADO = "aplicado"   # la sanción o bonificación está vigente
    ANULADO = "anulado"     # el administrador la perdonó (los puntos se devolvieron)
