from fastapi import FastAPI
from backend.usuarios.presentation.usuario_routes import router as usuario_router

app = FastAPI()


app.include_router(usuario_router, prefix="/api")


@app.get("/")
def inicio():
    return {"mensaje": "Backend funcionando"}
