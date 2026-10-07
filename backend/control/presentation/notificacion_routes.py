from fastapi import APIRouter

router = APIRouter(
    prefix="/notificaciones",
    tags=["Notificaciones"]
)


@router.get("/")
def listar_notificaciones():
    return {
        "mensaje": "Aquí se mostrarán las notificaciones"
    }