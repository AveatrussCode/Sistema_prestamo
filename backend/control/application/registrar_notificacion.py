from datetime import date
from backend.control.domain.notificacion import Notificacion


def registrar_notificacion(
    id_notificacion: int,
    id_destinatario: int,
    mensaje: str,
    motivo: str,
    fecha: date
) -> Notificacion:

    notificacion = Notificacion(
        id_notificacion=id_notificacion,
        id_destinatario=id_destinatario,
        mensaje=mensaje,
        motivo=motivo,
        fecha=fecha
    )

    return notificacion