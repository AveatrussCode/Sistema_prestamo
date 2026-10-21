from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass
class ReglaPrestamo:
    """Regla que rige los préstamos de una CATEGORÍA de objetos (RF24: políticas de préstamo).

    Cada categoría tiene su propia regla: no es lo mismo prestar una laptop (pocos días,
    1 a la vez) que un libro (más días, varios a la vez).

    Atributos del diagrama de clases:
      id_regla      : identificador (None mientras no se guarde en la base de datos)
      tiempo_maximo : días máximos que puede durar un préstamo de esa categoría
      max_objetos   : cuántos objetos DE ESA CATEGORÍA puede tener prestados un usuario a la vez
      condiciones   : texto informativo con las condiciones (se muestra al usuario)

    Atributos agregados (NO están en el diagrama, ver notas al final del archivo):
      categoria_id      : categoría a la que se aplica la regla (igual que Objeto.categoria_id)
      activa            : permite activar() / desactivar()
      max_renovaciones  : cuántas veces se puede renovar un préstamo (para puede_renovar)
    """

    categoria_id: int
    tiempo_maximo: int
    max_objetos: int
    condiciones: str = ""
    id_regla: Optional[int] = None
    activa: bool = True
    max_renovaciones: int = 1

    def __post_init__(self):
        if self.tiempo_maximo <= 0:
            raise ValueError("El tiempo máximo de préstamo debe ser mayor que 0 días.")
        if self.max_objetos <= 0:
            raise ValueError("El máximo de objetos debe ser mayor que 0.")
        if self.max_renovaciones < 0:
            raise ValueError("El máximo de renovaciones no puede ser negativo.")

    def aplica_a(self, categoria_id: int) -> bool:
        """True si esta regla es la que corresponde a objetos de esa categoría."""
        return self.categoria_id == categoria_id

    # ---------- UML: calcularFechaDevolucion() ----------

    def calcular_fecha_devolucion(self, fecha_inicio: date) -> date:
        """Última fecha de devolución que la regla permite para un préstamo que empieza en fecha_inicio."""
        return fecha_inicio + timedelta(days=self.tiempo_maximo)

    # ---------- UML: puedeRenovar() ----------

    def puede_renovar(self, renovaciones_hechas: int, esta_vencido: bool = False) -> bool:
        """True si la regla está activa, el préstamo no está vencido y aún quedan renovaciones."""
        return self.activa and not esta_vencido and renovaciones_hechas < self.max_renovaciones

    # ---------- UML: cumpleCondiciones() ----------

    def cumple_condiciones(self, fecha_inicio: date, fecha_devolucion_prevista: date,
                           prestamos_activos: int, cantidad_nueva: int = 1) -> bool:
        """True si el préstamo propuesto respeta la regla (activa, duración y cantidad de objetos)."""
        return self._motivo_incumplimiento(
            fecha_inicio, fecha_devolucion_prevista, prestamos_activos, cantidad_nueva
        ) is None

    def validar(self, fecha_inicio: date, fecha_devolucion_prevista: date,
                prestamos_activos: int, cantidad_nueva: int = 1) -> None:
        """Igual que cumple_condiciones, pero lanza ValueError explicando qué se incumple."""
        motivo = self._motivo_incumplimiento(
            fecha_inicio, fecha_devolucion_prevista, prestamos_activos, cantidad_nueva
        )
        if motivo is not None:
            raise ValueError(motivo)

    def _motivo_incumplimiento(self, fecha_inicio: date, fecha_devolucion_prevista: date,
                               prestamos_activos: int, cantidad_nueva: int) -> Optional[str]:
        if not self.activa:
            return "La regla de préstamo no está activa."
        if fecha_devolucion_prevista < fecha_inicio:
            return "La fecha de devolución no puede ser anterior a la de inicio."
        if (fecha_devolucion_prevista - fecha_inicio).days > self.tiempo_maximo:
            return (f"El préstamo excede el tiempo máximo de {self.tiempo_maximo} días "
                    f"(como máximo hasta el {self.calcular_fecha_devolucion(fecha_inicio)}).")
        if prestamos_activos + cantidad_nueva > self.max_objetos:
            return (f"El usuario ya tiene {prestamos_activos} objeto(s) prestado(s); "
                    f"el máximo permitido es {self.max_objetos}.")
        return None

    # ---------- UML: activar() / desactivar() ----------

    def activar(self) -> None:
        self.activa = True

    def desactivar(self) -> None:
        self.activa = False

