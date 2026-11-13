"""La clase REPORTE (la comparten todos los reportes). Pertenece al dominio de Control y Seguimiento.

Un Reporte es un documento generado con datos que ya existen en el sistema:
    Reporte
     ├─ titulo
     ├─ resumen  -> lista de DatoResumen  (los datos clave que se ven arriba)
     └─ tablas   -> lista de Tabla        (cada una con sus Columna y sus filas)

Son clases simples (dataclass): solo guardan datos. La lógica de cada reporte
vive en su propio servicio (application) y en sus clases de dominio.
"""
from dataclasses import dataclass, field


@dataclass
class Columna:
    clave: str    # nombre del campo dentro de cada fila, ej. "dias_atraso"
    titulo: str   # lo que lee el administrador en el encabezado, ej. "Días de atraso"


@dataclass
class DatoResumen:
    etiqueta: str            # ej. "Vencidos"
    valor: int | float | str  # ej. 3


@dataclass
class Tabla:
    titulo: str
    columnas: list[Columna]
    filas: list[dict]  # cada fila es {clave_de_columna: valor}


@dataclass
class Reporte:
    titulo: str
    resumen: list[DatoResumen] = field(default_factory=list)
    tablas: list[Tabla] = field(default_factory=list)
