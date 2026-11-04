from backend.usuarios.presentation.auth_routes import usuario_actual, CuentaModel
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.usuarios.infraestructure.usuario_repository import UsuarioRepository

router = APIRouter(prefix='/usuarios', tags=['Usuarios'])
MAX_BYTES = 5 * 1024 * 1024

def estudiante(usuario_id: int, db: Session):
    usuario = UsuarioRepository(db).obtener_por_id(usuario_id)
    if usuario is None:
        raise HTTPException(404, 'Usuario no encontrado.')
    if usuario.tipo != 'estudiante':
        raise HTTPException(400, 'La constancia solo corresponde a estudiantes.')
    return usuario

@router.put('/{usuario_id}/constancia-matricula')
async def subir_constancia(usuario_id: int, request: Request, db: Session = Depends(get_db), actor=Depends(usuario_actual)):
    if actor.id != usuario_id and (not actor.rol or actor.rol.nombre != "ADMIN"):
        raise HTTPException(403, "No puedes acceder a la constancia de otro usuario.")
    estudiante(usuario_id, db)
    if request.headers.get('content-type', '').split(';')[0] != 'application/pdf':
        raise HTTPException(415, 'Selecciona un archivo PDF.')
    contenido = bytearray()
    async for bloque in request.stream():
        if len(contenido) + len(bloque) > MAX_BYTES:
            raise HTTPException(413, 'El PDF no debe superar los 5 MB.')
        contenido.extend(bloque)
    
    from backend.usuarios.presentation.auth_routes import guardar_pdf
    guardar_pdf(usuario_id, bytes(contenido), db)
    return {'mensaje': 'Constancia de matrícula guardada correctamente.'}

@router.get('/{usuario_id}/constancia-matricula')
def descargar_constancia(usuario_id: int, db: Session = Depends(get_db), actor=Depends(usuario_actual)):
    if actor.id != usuario_id and (not actor.rol or actor.rol.nombre != "ADMIN"):
        raise HTTPException(403, "No puedes acceder a la constancia de otro usuario.")
    estudiante(usuario_id, db)
    
    cuenta = db.get(CuentaModel, usuario_id)
    if not cuenta or not cuenta.constancia_blob:
        raise HTTPException(404, 'El estudiante todavía no tiene una constancia.')
        
    return Response(content=cuenta.constancia_blob, media_type='application/pdf')