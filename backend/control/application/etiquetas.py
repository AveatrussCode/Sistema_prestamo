"""Textos legibles para los valores internos (así el administrador no lee "DANHADO" ni "NO_DISPONIBLE")."""

ESTADO_FISICO = {"BUENO": "Bueno", "REGULAR": "Regular", "DANHADO": "Dañado"}

DISPONIBILIDAD = {
    "DISPONIBLE": "Disponible",
    "PRESTADO": "Prestado",
    "RESERVADO": "Reservado",
    "NO_DISPONIBLE": "No disponible",
    "DADO_DE_BAJA": "Dado de baja",
}

ESTADO_RESERVA = {
    "PENDIENTE": "Pendiente",
    "CONFIRMADA": "Confirmada",
    "FINALIZADA": "Finalizada",
    "CANCELADA": "Cancelada",
    "VENCIDA": "Vencida",
}


def etiqueta(tabla: dict[str, str], valor: str | None) -> str:
    """Texto legible de `valor`; vacío si no hay valor; el valor tal cual si no está en la tabla."""
    if not valor:
        return ""
    return tabla.get(valor, valor)


def fecha(valor) -> str:
    """Fecha en formato ISO (la pantalla la muestra como dd/mm/aaaa); vacío si no hay fecha."""
    return valor.isoformat() if valor else ""
