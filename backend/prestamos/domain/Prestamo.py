
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

    def registrar_devolucion(self, fecha: date | None = None):
        if self.estado != EstadoPrestamo.ACTIVO:
            raise ValueError("El préstamo no está activo")

        fecha = fecha or date.today()
        self.fecha_devolucion_real = fecha
        self.estado = EstadoPrestamo.DEVUELTO

    def cancelar(self):
        if self.estado != EstadoPrestamo.ACTIVO:
            raise ValueError("Solo se puede cancelar un préstamo activo")

        self.estado = EstadoPrestamo.CANCELADO

    def puede_renovarse(self) -> bool:
        return (
            self.estado == EstadoPrestamo.ACTIVO
            and not self.esta_vencido()
        )




