"""Envío de correos. Modo consola por defecto; SMTP cuando se configura en .env."""
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

MODO = os.getenv("MAIL_MODE", "console").lower()  # "console" o "smtp"
FROM = os.getenv("MAIL_FROM", "no-reply@epcc.unsa.edu.pe")


def _enviar_smtp(destinatario: str, asunto: str, cuerpo: str):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    if not (host and user and password):
        print(f"⚠️  SMTP no configurado. Correo NO enviado a {destinatario}")
        return
    msg = EmailMessage()
    msg["From"] = FROM
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.set_content(cuerpo)
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)


def _enviar_consola(destinatario: str, asunto: str, cuerpo: str):
    print("\n" + "=" * 60)
    print(f"📧 CORREO SIMULADO → {destinatario}")
    print(f"Asunto: {asunto}")
    print(f"Fecha:  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("-" * 60)
    print(cuerpo)
    print("=" * 60 + "\n")


def enviar_correo(destinatario: str, asunto: str, cuerpo: str):
    if MODO == "smtp":
        _enviar_smtp(destinatario, asunto, cuerpo)
    else:
        _enviar_consola(destinatario, asunto, cuerpo)


# ---- Plantillas ----

def correo_solicitud_recibida(nombre: str, correo: str, tipo: str):
    asunto = "Solicitud de cuenta recibida — Sistema de Préstamos EPCC"
    cuerpo = f"""Hola {nombre},

Hemos recibido tu solicitud para crear una cuenta de {tipo} en el Sistema de Préstamos de la EPCC.

Un administrador revisará tu información. Te avisaremos por este mismo correo cuando tu cuenta sea aprobada o si necesitamos más datos.

Gracias por tu paciencia.

— Sistema de Préstamos · EPCC UNSA"""
    enviar_correo(correo, asunto, cuerpo)


def correo_aprobacion(nombre: str, correo: str):
    asunto = "✅ Tu cuenta fue aprobada — Sistema de Préstamos EPCC"
    cuerpo = f"""Hola {nombre},

Tu solicitud ha sido revisada y APROBADA. Ya puedes iniciar sesión con tu correo institucional y la contraseña que registraste.

Ingresa en: http://localhost:5173

— Sistema de Préstamos · EPCC UNSA"""
    enviar_correo(correo, asunto, cuerpo)


def correo_rechazo(nombre: str, correo: str, motivo: str):
    asunto = "❌ Tu solicitud fue rechazada — Sistema de Préstamos EPCC"
    cuerpo = f"""Hola {nombre},

Hemos revisado tu solicitud y en esta ocasión no pudimos aprobarla.

Motivo: {motivo}

Si crees que es un error o puedes corregir la información, responde a este correo o contacta al administrador.

— Sistema de Préstamos · EPCC UNSA"""
    enviar_correo(correo, asunto, cuerpo)