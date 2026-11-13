"""Un equipo que salió en préstamo y todavía NO se devolvió (clase de dominio del reporte de pendientes).

Reutiliza la entidad Prestamo y su regla `esta_vencido()` que ya existe en el contexto de Préstamos,
así la regla de "vencido" se define en un solo lugar.
"""
from dataclasses import dataclass
from datetime import date

from backend.prestamos.domain.Prestamo import Prestamo


@dataclass
class PendienteDevolucion:
    prestamo: Prestamo
    usuario: str          # quién lo tiene
    correo: str | None    # para avisarle (None si el usuario fue eliminado)
    equipo: str           # qué se llevó

    def esta_vencido(self) -> bool:
        return self.prestamo.esta_vencido()

    def dias_de_atraso(self) -> int:
        """Días pasados desde la fecha prevista de devolución (0 si todavía está en plazo)."""
        return max((date.today() - self.prestamo.fecha_devolucion_prevista).days, 0)
