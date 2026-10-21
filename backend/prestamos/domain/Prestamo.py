
from dataclasses import dataclass
from datetime import date

from backend.prestamos.domain.enums import EstadoPrestamo


@dataclass
class Prestamo:
    id_prestamo: int
    id_usuario: int
    id_objeto: int
    fecha_inicio: date
    fecha_devolucion_prevista: date
    fecha_devolucion_real: date | None = None
    estado: EstadoPrestamo = EstadoPrestamo.ACTIVO

    def esta_vencido(self) -> bool:
        return (
            self.estado == EstadoPrestamo.ACTIVO
            and date.today() > self.fecha_devolucion_prevista
        )

    def registrar_devolucion(
        self,
        fecha: date | None = None,
    ) -> None:
        if self.estado != EstadoPrestamo.ACTIVO:
            raise ValueError("El préstamo no está activo")

        fecha_retorno = fecha or date.today()

        if fecha_retorno < self.fecha_inicio:
            raise ValueError(
                "La devolución no puede ser anterior al inicio del préstamo"
            )

        self.fecha_devolucion_real = fecha_retorno
        self.estado = EstadoPrestamo.DEVUELTO

    def cancelar(self) -> None:
        if self.estado != EstadoPrestamo.ACTIVO:
            raise ValueError(
                "Solo se puede cancelar un préstamo activo"
            )

        self.estado = EstadoPrestamo.CANCELADO

    def puede_renovarse(self) -> bool:
        return (
            self.estado == EstadoPrestamo.ACTIVO
            and not self.esta_vencido()
        )

    def renovar(self, nueva_fecha: date) -> None:
        if not self.puede_renovarse():
            raise ValueError(
                "El préstamo no puede renovarse"
            )

        if nueva_fecha <= self.fecha_devolucion_prevista:
            raise ValueError(
                "La nueva fecha debe ser posterior a la fecha prevista actual"
            )

        self.fecha_devolucion_prevista = nueva_fecha
