"""
Utilidades y funciones auxiliares para el sistema de SMS
Validaciones, formato de datos, conversiones
"""
import re
import logging
from typing import List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class PhoneValidator:
    """Validador de números telefónicos"""

    @staticmethod
    def validate_number(number: str, country_code: str = None) -> bool:
        """
        Validar número telefónico

        Args:
            number: Número a validar
            country_code: Código de país (ej: '57' para Colombia)

        Returns:
            True si es válido, False en caso contrario
        """
        # Remover espacios y caracteres especiales
        cleaned = re.sub(r'\D', '', str(number))

        # Si no hay país especificado, validar longitud mínima
        if not country_code:
            return len(cleaned) >= 7

        # Validar que tenga el código de país
        if not cleaned.startswith(country_code):
            cleaned = country_code + cleaned

        # Validar longitud total (típicamente 10-15 dígitos)
        return 7 <= len(cleaned) <= 15

    @staticmethod
    def format_number(number: str, country_code: str = None) -> str:
        """
        Formatear número telefónico

        Args:
            number: Número sin formato
            country_code: Código de país a añadir

        Returns:
            Número formateado
        """
        # Remover todo excepto números
        cleaned = re.sub(r'\D', '', str(number))

        # Agregar código de país si se proporciona y no lo tiene
        if country_code and not cleaned.startswith(country_code):
            cleaned = country_code + cleaned

        return cleaned

    @staticmethod
    def validate_phone_list(numbers: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validar lista de números

        Args:
            numbers: Lista de números

        Returns:
            Tupla (números_válidos, números_inválidos)
        """
        valid = []
        invalid = []

        for num in numbers:
            if PhoneValidator.validate_number(num):
                valid.append(num)
            else:
                invalid.append(num)

        return valid, invalid


class MessageValidator:
    """Validador de mensajes SMS"""

    # Caracteres sensibles que pueden causar problemas
    SENSITIVE_CHARS = {
        '\x00': 'NUL',
        '\x1a': 'SUB',
    }

    # Caracteres que requieren escapado
    SPECIAL_CHARS = {
        '"': '\\"',
        '\\': '\\\\',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t'
    }

    @staticmethod
    def validate_content(content: str, max_length: int = 1024) -> Tuple[bool, str]:
        """
        Validar contenido del mensaje

        Args:
            content: Contenido a validar
            max_length: Longitud máxima permitida

        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not content:
            return False, "Contenido vacío"

        if len(content) > max_length:
            return False, f"Contenido demasiado largo (máx {max_length} caracteres)"

        # Verificar caracteres sensibles
        for char, name in MessageValidator.SENSITIVE_CHARS.items():
            if char in content:
                return False, f"Contiene carácter sensible: {name}"

        return True, "Válido"

    @staticmethod
    def sanitize_content(content: str) -> str:
        """
        Sanitizar contenido del mensaje

        Args:
            content: Contenido sin sanitizar

        Returns:
            Contenido sanitizado
        """
        result = content

        # Remover caracteres sensibles
        for char in MessageValidator.SENSITIVE_CHARS:
            result = result.replace(char, '')

        return result

    @staticmethod
    def escape_json_string(content: str) -> str:
        """
        Escapar string para JSON

        Args:
            content: String a escapar

        Returns:
            String escapado
        """
        result = content
        for special, escaped in MessageValidator.SPECIAL_CHARS.items():
            result = result.replace(special, escaped)
        return result


class TimeValidator:
    """Validador de tiempos y fechas"""

    DATE_FORMAT = "%Y%m%d%H%M%S"  # Formato esperado: 20171001123015

    @staticmethod
    def validate_sendtime(sendtime: str) -> Tuple[bool, str]:
        """
        Validar formato de sendtime

        Args:
            sendtime: String en formato YYYYMMDDHHmmss

        Returns:
            Tupla (es_válido, mensaje)
        """
        if not sendtime:
            return False, "sendtime vacío"

        if len(sendtime) != 14:
            return False, "sendtime debe tener 14 caracteres (YYYYMMDDHHmmss)"

        try:
            datetime.strptime(sendtime, TimeValidator.DATE_FORMAT)
            return True, "Válido"
        except ValueError:
            return False, "Formato inválido (debe ser YYYYMMDDHHmmss)"

    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """
        Convertir datetime a formato Traffilink

        Args:
            dt: Objeto datetime

        Returns:
            String en formato YYYYMMDDHHmmss
        """
        return dt.strftime(TimeValidator.DATE_FORMAT)


class SMSStatistics:
    """Clase para gestionar estadísticas de SMS"""

    def __init__(self):
        self.total_sent = 0
        self.total_failed = 0
        self.total_delivered = 0
        self.total_undelivered = 0
        self.total_balance_used = 0

    def add_sent(self, count: int = 1):
        """Agregar SMS enviados"""
        self.total_sent += count
        logger.info(f"📊 SMS enviados: {self.total_sent}")

    def add_failed(self, count: int = 1):
        """Agregar SMS fallidos"""
        self.total_failed += count
        logger.warning(f"⚠️  SMS fallidos: {self.total_failed}")

    def add_delivered(self, count: int = 1):
        """Agregar SMS entregados"""
        self.total_delivered += count

    def add_undelivered(self, count: int = 1):
        """Agregar SMS no entregados"""
        self.total_undelivered += count

    def subtract_balance(self, amount: float):
        """Restar balance usado"""
        self.total_balance_used += amount

    def get_summary(self) -> dict:
        """Obtener resumen de estadísticas"""
        return {
            "total_enviados": self.total_sent,
            "total_fallidos": self.total_failed,
            "total_entregados": self.total_delivered,
            "total_no_entregados": self.total_undelivered,
            "balance_usado": self.total_balance_used,
            "tasa_exito": (
                (self.total_sent - self.total_failed) / self.total_sent * 100
                if self.total_sent > 0 else 0
            )
        }

    def print_summary(self):
        """Imprimir resumen de estadísticas"""
        summary = self.get_summary()
        print("\n" + "="*50)
        print("📊 RESUMEN DE ESTADÍSTICAS")
        print("="*50)
        print(f"✅ SMS Enviados: {summary['total_enviados']}")
        print(f"❌ SMS Fallidos: {summary['total_fallidos']}")
        print(f"✅ SMS Entregados: {summary['total_entregados']}")
        print(f"📭 SMS No Entregados: {summary['total_no_entregados']}")
        print(f"💰 Balance Usado: {summary['balance_usado']}")
        print(f"📈 Tasa de Éxito: {summary['tasa_exito']:.2f}%")
        print("="*50 + "\n")


if __name__ == "__main__":
    # Test validadores
    print("🧪 Prueba de Validadores\n")

    # Test teléfono
    print("1️⃣  Validador de Teléfono:")
    test_nums = ["3001234567", "123", "+573001234567", "invalid"]
    for num in test_nums:
        valid = PhoneValidator.validate_number(num)
        print(f"  {num}: {'✅' if valid else '❌'}")

    # Test mensaje
    print("\n2️⃣  Validador de Mensaje:")
    test_msgs = ["Hola", "a" * 2000, ""]
    for msg in test_msgs:
        valid, msg_err = MessageValidator.validate_content(msg)
        print(f"  '{msg[:20]}...': {'✅' if valid else f'❌ {msg_err}'}")

    # Test tiempo
    print("\n3️⃣  Validador de Tiempo:")
    test_times = ["20240101120000", "2024-01-01", "invalid"]
    for time_str in test_times:
        valid, msg_err = TimeValidator.validate_sendtime(time_str)
        print(f"  {time_str}: {'✅' if valid else f'❌ {msg_err}'}")
