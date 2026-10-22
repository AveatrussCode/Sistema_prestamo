// Único lugar que sabe "cómo hablar con el backend". Todas las pantallas pasan por aquí.

// Dirección del backend. Para cambiarla crea frontend/.env con:  VITE_API_URL=http://localhost:8000
export const API_URL: string = import.meta.env.VITE_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`;

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// FastAPI devuelve {"detail": "texto"} en errores de negocio y {"detail": [{msg: ...}]} en errores de validación.
function detalleATexto(detalle: unknown, respaldo: string): string {
  if (typeof detalle === "string") return detalle;
  if (Array.isArray(detalle)) {
    return detalle.map((d) => (d && typeof d.msg === "string" ? d.msg : String(d))).join(" · ");
  }
  return respaldo;
}

interface Opciones {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
}

export async function api<T>(ruta: string, opciones: Opciones = {}): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(`${API_URL}${ruta}`, {
      method: opciones.method ?? "GET",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: opciones.body === undefined ? undefined : JSON.stringify(opciones.body),
    });
  } catch {
    // fetch solo "lanza" si no pudo ni llegar al servidor (apagado, URL mala, CORS...)
    throw new ApiError(0, "No se pudo conectar con el servidor. ¿Está encendido el backend (uvicorn)?");
  }

  if (!respuesta.ok) {
    let mensaje = `Error ${respuesta.status}`;
    try {
      const cuerpo = await respuesta.json();
      mensaje = detalleATexto(cuerpo.detail, mensaje);
    } catch {
      // la respuesta de error no traía JSON; nos quedamos con el mensaje genérico
    }
    throw new ApiError(respuesta.status, mensaje);
  }
  return (await respuesta.json()) as T;
}
