from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from backend.prestamos.domain.enums import TipoEventoPrestamo


@dataclass(frozen=True)
class HistorialPrestamo:
    
    """UN registro del historial: un evento que ocurrió en un préstamo (RF15, RF16).

    Es inmutable (frozen): un historial no se edita ni se corrige, solo se agregan registros nuevos.

    Atributos del diagrama de clases:
      id_historial : identificador (None hasta que se guarde en la base de datos)
      fecha        : cuándo ocurrió el evento
      tipo         : qué ocurrió (ver TipoEventoPrestamo)
      detalle      : texto libre con más información

    Atributos agregados (NO están en el diagrama, ver notas al final del archivo):
      id_prestamo, id_usuario, id_objeto : a qué préstamo, usuario y objeto corresponde el evento
    """

    id_prestamo: int
    id_usuario: int
    id_objeto: int
    tipo: TipoEventoPrestamo
    detalle: str = ""
    fecha: date = field(default_factory=date.today)
    id_historial: Optional[int] = None

    def __post_init__(self):
        if not isinstance(self.tipo, TipoEventoPrestamo):
            raise ValueError(
                "El tipo de evento debe ser un TipoEventoPrestamo "
                f"(INICIADO, RENOVADO, DEVUELTO, CANCELADO o VENCIDO), no {self.tipo!r}."
            )

    # ---------- UML: registrarEvento() ----------

    @classmethod
    def registrar_evento(cls, id_prestamo: int, id_usuario: int, id_objeto: int,
                         tipo: TipoEventoPrestamo, detalle: str = "",
                         fecha: Optional[date] = None) -> "HistorialPrestamo":
        """Crea el registro de un evento. Si no se indica fecha, usa la de hoy."""
        return cls(id_prestamo=id_prestamo, id_usuario=id_usuario, id_objeto=id_objeto,
                   tipo=tipo, detalle=detalle, fecha=fecha or date.today())

