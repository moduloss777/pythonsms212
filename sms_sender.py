"""
Gestor completo de envío de SMS
Maneja validación, fragmentación, cola y reintentos
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from uuid import uuid4
from traffilink_api import TrafficLinkAPI
from utils import PhoneValidator, MessageValidator
from database import Database
from cache import Cache
from config import SMS_LIMIT_POST, MAX_MESSAGE_LENGTH

logger = logging.getLogger(__name__)


class SMSSender:
    """Gestor principal de envío de SMS"""

    def __init__(self):
        """Inicializar gestor de envío"""
        self.api = TrafficLinkAPI()
        self.db = Database()
        self.cache = Cache(max_size=500, default_ttl=600)
        self.sent_count = 0
        self.failed_count = 0
        self.duplicates_removed = 0

    def validate_and_prepare(self, numbers: List[str], content: str,
                            sender: Optional[str] = None) -> Tuple[bool, List[str], str]:
        """
        Validar y preparar números y contenido

        Args:
            numbers: Lista de números
            content: Contenido del mensaje
            sender: Remitente opcional

        Returns:
            Tupla (es_válido, números_válidos, mensaje_error)
        """
        # Validar números
        valid_numbers, invalid_numbers = PhoneValidator.validate_phone_list(numbers)

        if invalid_numbers:
            logger.warning(f"⚠️  {len(invalid_numbers)} números inválidos ignorados: {invalid_numbers[:5]}")

        if not valid_numbers:
            return False, [], "No hay números válidos para enviar"

        # Eliminar duplicados
        unique_numbers = list(set(valid_numbers))
        if len(unique_numbers) < len(valid_numbers):
            self.duplicates_removed += len(valid_numbers) - len(unique_numbers)
            logger.info(f"🔄 Duplicados removidos: {self.duplicates_removed}")

        # Validar contenido
        is_valid, error_msg = MessageValidator.validate_content(content)
        if not is_valid:
            return False, [], error_msg

        # Sanitizar contenido
        sanitized_content = MessageValidator.sanitize_content(content)

        return True, unique_numbers, sanitized_content

    def fragment_message(self, content: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
        """
        Fragmentar mensaje si es demasiado largo

        Args:
            content: Contenido a fragmentar
            max_length: Longitud máxima por fragmento

        Returns:
            Lista de fragmentos
        """
        if len(content) <= max_length:
            return [content]

        fragments = []
        words = content.split()
        current_fragment = ""

        for word in words:
            if len(current_fragment) + len(word) + 1 <= max_length:
                current_fragment += word + " "
            else:
                if current_fragment:
                    fragments.append(current_fragment.strip())
                current_fragment = word + " "

        if current_fragment:
            fragments.append(current_fragment.strip())

        logger.info(f"📄 Mensaje fragmentado en {len(fragments)} partes")
        return fragments

    def optimize_numbers(self, numbers: List[str]) -> List[str]:
        """
        Optimizar lista de números (formato, eliminación de duplicados)

        Args:
            numbers: Lista de números

        Returns:
            Lista optimizada
        """
        optimized = []

        for num in numbers:
            # Formatear número
            formatted = PhoneValidator.format_number(num)
            if formatted not in optimized:
                optimized.append(formatted)

        return optimized

    def send_sms(self, numbers: List[str], content: str,
                sender: Optional[str] = None, sendtime: Optional[str] = None,
                use_fragmenting: bool = True) -> Dict:
        """
        Enviar SMS con validación y fragmentación

        Args:
            numbers: Números de teléfono
            content: Contenido del mensaje
            sender: Remitente opcional
            sendtime: Tiempo de envío opcional
            use_fragmenting: Fragmentar si es necesario

        Returns:
            Dict con resultado de envío
        """
        logger.info(f"📤 Iniciando envío a {len(numbers)} números...")

        # Validar y preparar
        is_valid, valid_numbers, processed_content = self.validate_and_prepare(
            numbers, content, sender
        )

        if not is_valid:
            logger.error(f"❌ Validación fallida: {processed_content}")
            return {
                "code": -100,
                "error_message": processed_content,
                "sms_count": 0,
                "sent_ids": []
            }

        # Optimizar números
        optimized_numbers = self.optimize_numbers(valid_numbers)

        # Fragmentar si es necesario
        fragments = [processed_content]
        if use_fragmenting and len(processed_content) > MAX_MESSAGE_LENGTH:
            fragments = self.fragment_message(processed_content)

        sent_ids = []
        total_sent = 0

        # Enviar cada fragmento
        for fragment_idx, fragment in enumerate(fragments):
            logger.info(f"📨 Enviando fragmento {fragment_idx + 1}/{len(fragments)}")

            # Dividir en lotes si es necesario
            for i in range(0, len(optimized_numbers), SMS_LIMIT_POST):
                batch = optimized_numbers[i:i + SMS_LIMIT_POST]

                try:
                    result = self.api.send_sms(
                        numbers=batch,
                        content=fragment,
                        sender=sender,
                        sendtime=sendtime,
                        use_post=True if len(batch) > 100 else False
                    )

                    if result.get('code') == 0:
                        sms_id = result.get('id')
                        sent_ids.append(sms_id)
                        total_sent += len(batch)
                        self.sent_count += len(batch)

                        # Guardar en base de datos
                        self.db.save_sms(
                            sms_id, "0152C274", batch,
                            fragment, sender, sendtime
                        )

                        logger.info(f"✅ Lote enviado: {len(batch)} SMS - ID: {sms_id}")

                    else:
                        error_msg = result.get('error_message')
                        logger.error(f"❌ Error en lote: {error_msg}")
                        self.failed_count += len(batch)

                except Exception as e:
                    logger.error(f"❌ Excepción al enviar: {str(e)}")
                    self.failed_count += len(batch)

        return {
            "code": 0 if sent_ids else -101,
            "message": "SMS enviados exitosamente" if sent_ids else "No se pudo enviar ningún SMS",
            "sms_count": total_sent,
            "fragments": len(fragments),
            "batches": (len(optimized_numbers) + SMS_LIMIT_POST - 1) // SMS_LIMIT_POST,
            "sent_ids": sent_ids,
            "duplicates_removed": self.duplicates_removed
        }

    def send_bulk(self, numbers: List[str], content: str,
                 sender: Optional[str] = None) -> Dict:
        """
        Envío en masa con optimizaciones

        Args:
            numbers: Números de teléfono
            content: Contenido
            sender: Remitente

        Returns:
            Resultado de envío
        """
        logger.info(f"📦 Enviando en masa a {len(numbers)} contactos...")

        result = self.send_sms(
            numbers=numbers,
            content=content,
            sender=sender,
            use_fragmenting=True
        )

        return result

    def get_statistics(self) -> Dict:
        """Obtener estadísticas de envíos"""
        return {
            "total_sent": self.sent_count,
            "total_failed": self.failed_count,
            "duplicates_removed": self.duplicates_removed,
            "success_rate": (
                (self.sent_count / (self.sent_count + self.failed_count) * 100)
                if (self.sent_count + self.failed_count) > 0 else 0
            )
        }

    def reset_statistics(self):
        """Resetear estadísticas"""
        self.sent_count = 0
        self.failed_count = 0
        self.duplicates_removed = 0
        logger.info("🔄 Estadísticas reseteadas")


class SMSRetry:
    """Gestor de reintentos para SMS fallidos"""

    def __init__(self, max_retries: int = 3, delay_seconds: int = 5):
        """
        Inicializar gestor de reintentos

        Args:
            max_retries: Máximo número de reintentos
            delay_seconds: Segundos entre reintentos
        """
        self.sender = SMSSender()
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds
        self.retry_queue = []

    def add_to_retry_queue(self, sms_id: str, numbers: List[str],
                          content: str, attempt: int = 1):
        """
        Agregar SMS a cola de reintentos

        Args:
            sms_id: ID del SMS
            numbers: Números
            content: Contenido
            attempt: Intento actual
        """
        self.retry_queue.append({
            "sms_id": sms_id,
            "numbers": numbers,
            "content": content,
            "attempt": attempt,
            "added_at": datetime.now()
        })

        logger.warning(f"⚠️  SMS agregado a cola de reintentos: {sms_id} (intento {attempt})")

    def retry_failed_sms(self):
        """Reintentar SMS en la cola"""
        if not self.retry_queue:
            logger.debug("📭 Cola de reintentos vacía")
            return

        logger.info(f"🔄 Reintentando {len(self.retry_queue)} SMS fallidos...")

        for item in self.retry_queue[:]:
            if item["attempt"] <= self.max_retries:
                logger.info(f"🔄 Reintentando {item['sms_id']} (intento {item['attempt'] + 1})")

                result = self.sender.send_sms(
                    numbers=item["numbers"],
                    content=item["content"]
                )

                if result.get('code') == 0:
                    logger.info(f"✅ Reintento exitoso: {item['sms_id']}")
                    self.retry_queue.remove(item)
                else:
                    item["attempt"] += 1
                    item["added_at"] = datetime.now()
            else:
                logger.error(f"❌ SMS descartado después de {self.max_retries} reintentos: {item['sms_id']}")
                self.retry_queue.remove(item)

    def get_queue_status(self) -> Dict:
        """Obtener estado de la cola"""
        return {
            "queue_size": len(self.retry_queue),
            "items": self.retry_queue
        }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL GESTOR DE ENVÍO")
    print("="*60 + "\n")

    sender = SMSSender()

    # Test 1: Validación
    print("1️⃣  Validando números y contenido...")
    is_valid, valid_nums, content = sender.validate_and_prepare(
        ["3001234567", "123", "3007654321"],
        "Mensaje de prueba"
    )
    print(f"   Válido: {is_valid}")
    print(f"   Números: {valid_nums}\n")

    # Test 2: Envío simulado
    print("2️⃣  Preparando envío...")
    print(f"   Números optimizados: {sender.optimize_numbers(['3001234567', '3001234567'])}\n")

    # Test 3: Estadísticas
    print("3️⃣  Estadísticas:")
    print(f"   {sender.get_statistics()}\n")

    sender.db.disconnect()

    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
