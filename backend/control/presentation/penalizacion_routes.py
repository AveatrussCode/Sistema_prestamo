from fastapi import APIRouter

router = APIRouter(
    prefix="/penalizaciones",
    tags=["Penalizaciones"]
)


@router.get("/")
def listar_penalizaciones():
    return {
        "mensaje": "Aquí se mostrarán las penalizaciones"
    }