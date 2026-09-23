from fastapi import APIRouter

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


@router.get("/")
def listar_usuarios():
    return {
        "mensaje": "Aquí se mostrarán los usuarios"
    }