"""Comunicación con Telegram mediante la Bot API (solo peticiones HTTP, sin librerías extra)."""
import requests

from . import config

LIMITE_MENSAJE = 4000          # Telegram acepta hasta 4096 caracteres por mensaje


def _url(metodo):
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN (créalo con @BotFather).")
    return f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{metodo}"


def _pedir(verbo, metodo, **opciones):
    """Llama a la Bot API. Si la red falla, el error nunca incluye la URL (que lleva el token)."""
    try:
        return requests.request(verbo, _url(metodo), **opciones)
    except requests.RequestException as error:
        raise requests.ConnectionError(f"Sin conexión con Telegram ({type(error).__name__})") from None


def enviar(chat_id, texto):
    respuesta = _pedir("POST", "sendMessage",
                       data={"chat_id": chat_id, "text": texto[:LIMITE_MENSAJE]}, timeout=20)
    datos = respuesta.json()
    if not datos.get("ok"):
        raise RuntimeError(f"Telegram rechazó el mensaje: {datos.get('description')}")
    return datos


def verificar_bot():
    """Devuelve el @usuario del bot o lanza un error claro si el token es inválido."""
    datos = _pedir("GET", "getMe", timeout=20).json()
    if not datos.get("ok"):
        raise RuntimeError("Token de Telegram inválido. Revísalo con @BotFather.")
    return datos["result"]["username"]


def preparar_polling():
    """Quita un webhook previo; si existe, getUpdates no funciona."""
    _pedir("GET", "deleteWebhook", timeout=20)


def obtener_mensajes(offset=None, espera=0):
    """Mensajes pendientes. Telegram los guarda hasta 24 h si nadie los lee."""
    parametros = {"timeout": espera}
    if offset is not None:
        parametros["offset"] = offset
    datos = _pedir("GET", "getUpdates", params=parametros, timeout=espera + 15).json()
    if not datos.get("ok"):
        raise RuntimeError(f"getUpdates falló: {datos.get('description')}")
    return datos["result"]


def confirmar_leidos(ultimo_update_id):
    """Marca como leídos todos los mensajes hasta ese id, para no procesarlos dos veces."""
    obtener_mensajes(offset=ultimo_update_id + 1)


def chat_autorizado(chat_id):
    """Solo el chat de TELEGRAM_CHAT_ID puede usar el bot; si falta, nadie (cerrado por omisión)."""
    return bool(config.TELEGRAM_CHAT_ID) and str(chat_id) == config.TELEGRAM_CHAT_ID
