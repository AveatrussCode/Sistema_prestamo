from datetime import date

from backend.control.domain.penalizacion import Penalizacion


def registrar_penalizacion(
    id_penalizacion: int,
    id_usuario: int,
    motivo: str,
    monto: float,
    fecha: date
) -> Penalizacion:

    penalizacion = Penalizacion(
        id_penalizacion=id_penalizacion,
        id_usuario=id_usuario,
        motivo=motivo,
        monto=monto,
        fecha=fecha
    )

    return penalizacion