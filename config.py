"""
Configuración centralizada para Traffilink API
Almacena variables de entorno y constantes del sistema
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ==================== TRAFFILINK API CONFIG ====================
TRAFFILINK_BASE_URL = os.getenv("TRAFFILINK_BASE_URL", "http://47.236.91.242:20003")
TRAFFILINK_ACCOUNT = os.getenv("TRAFFILINK_ACCOUNT", "0152C274")
TRAFFILINK_PASSWORD = os.getenv("TRAFFILINK_PASSWORD", "G2o0jRnm")

# ==================== PARAMETROS DE LA API ====================
# Límites de envío según método
SMS_LIMIT_GET = 100
SMS_LIMIT_POST = 10000

# Límites de reportes y SMS entrantes
REPORT_BATCH_LIMIT = 200
INCOMING_SMS_LIMIT = 50

# Máxima longitud de mensaje
MAX_MESSAGE_LENGTH = 1024

# ==================== ENCODING ====================
ENCODING = "utf-8"
CONTENT_TYPE = "application/json;charset=utf-8"

# ==================== CÓDIGOS DE ERROR ====================
ERROR_CODES = {
    0: "✅ Éxito",
    -1: "❌ Error de autenticación (account/password inválido)",
    -2: "❌ Parámetro 'numbers' vacío",
    -3: "❌ Contiene caracteres sensibles",
    -4: "❌ Error en formato JSON",
    -5: "❌ SMS demasiado largo (máx 1024 caracteres)",
    -6: "❌ Parámetro 'content' vacío",
    -7: "❌ Parámetro 'content' duplicado",
    -8: "❌ Parámetro 'sendtime' inválido",
    -9: "❌ Parámetro 'sender' inválido",
    -10: "❌ Saldo insuficiente",
    -11: "❌ Parámetro 'task' inválido",
    -12: "❌ Parámetro 'contacts' vacío"
}

# ==================== TIPOS DE TAREAS ====================
TASK_TYPES = {
    0: "Inmediata",
    1: "Programada (fecha/hora específica)",
    2: "Intervalo (cada X horas)",
    3: "Diaria (mismo tiempo cada día)",
    4: "Semanal (mismo día y hora)",
    5: "Mensual (mismo día y hora)"
}

# ==================== ESTADOS DE SMS ====================
SMS_STATUS = {
    "sent": "✅ Enviado",
    "failed": "❌ Falló",
    "delivery_success": "✅ Entregado",
    "delivery_failed": "❌ No entregado"
}

# ==================== CONFIGURACIÓN DE LOGGING ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "traffilink.log"
