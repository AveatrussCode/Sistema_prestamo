
from enum import enum

class EstadoReserva(str, Enum):
    PENDIENTE = "PENDIENTE"      # recién creada
    CONFIRMADA = "CONFIRMADA"    # aprobada por un administrativo
    FINALIZADA = "FINALIZADA"    # ya se usó (se convirtió en préstamo / terminó)
    CANCELADA = "CANCELADA"
    VENCIDA = "VENCIDA"          # pasó su fecha_fin sin finalizarse
