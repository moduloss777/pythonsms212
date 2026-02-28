"""
Tests unitarios para el módulo de envío de SMS
Verifica validación, fragmentación y procesamiento
"""
import unittest
import sys
from pathlib import Path

# Agregar parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sms_sender import SMSSender, SMSRetry
from message_processor import MessageProcessor, MessageTemplate
from sms_queue import SMSQueue, SMSPriority, SMSTask


class TestSMSSender(unittest.TestCase):
    """Tests para SMSSender"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.sender = SMSSender()

    def test_validate_numbers(self):
        """Probar validación de números"""
        is_valid, nums, content = self.sender.validate_and_prepare(
            ["3001234567", "invalid", "3007654321"],
            "Test message"
        )
        print(f"\n✓ Validación: {is_valid}")
        print(f"  Números válidos: {len(nums)}")
        self.assertTrue(is_valid)
        self.assertEqual(len(nums), 2)

    def test_optimize_numbers(self):
        """Probar optimización de números"""
        optimized = self.sender.optimize_numbers(
            ["3001234567", "3001234567", "3007654321"]
        )
        print(f"\n✓ Números duplicados removidos")
        print(f"  Original: 3, Optimizado: {len(optimized)}")
        self.assertEqual(len(optimized), 2)

    def test_fragment_message(self):
        """Probar fragmentación de mensaje"""
        long_message = "a" * 2000
        fragments = self.sender.fragment_message(long_message, max_length=1024)
        print(f"\n✓ Mensaje fragmentado")
        print(f"  Longitud original: {len(long_message)}, Fragmentos: {len(fragments)}")
        self.assertGreater(len(fragments), 1)

    def test_statistics(self):
        """Probar estadísticas"""
        self.sender.sent_count = 10
        self.sender.failed_count = 2
        stats = self.sender.get_statistics()
        print(f"\n✓ Estadísticas: {stats}")
        self.assertIn("total_sent", stats)
        self.assertIn("success_rate", stats)


class TestMessageProcessor(unittest.TestCase):
    """Tests para MessageProcessor"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.processor = MessageProcessor()

    def test_normalize_text(self):
        """Probar normalización de texto"""
        text = "Hola, ¿cómo estás?"
        normalized = self.processor.normalize_text(text)
        print(f"\n✓ Normalización: {text} → {normalized}")
        self.assertNotIn("á", normalized)

    def test_remove_emojis(self):
        """Probar remover emojis"""
        text = "Hola 👋 mundo 🌍"
        cleaned = self.processor.replace_emojis(text, preserve_emojis=False)
        print(f"\n✓ Emojis removidos: {text} → {cleaned}")
        self.assertNotIn("👋", cleaned)

    def test_replace_variables(self):
        """Probar reemplazo de variables"""
        text = "Hola {{name}}, tienes {{discount}}% de descuento"
        result = self.processor.replace_variables(
            text,
            {"name": "Juan", "discount": "50"}
        )
        print(f"\n✓ Variables reemplazadas: {result}")
        self.assertEqual(result, "Hola Juan, tienes 50% de descuento")

    def test_process_complete(self):
        """Probar procesamiento completo"""
        result = self.processor.process(
            "Hola 🌍",
            options={"remove_emojis": True, "normalize_accents": True}
        )
        print(f"\n✓ Procesamiento completo")
        print(f"  Original: {result['original']}")
        print(f"  Procesado: {result['processed']}")
        print(f"  Válido: {result['is_valid']}")
        self.assertTrue(result["is_valid"])


class TestMessageTemplate(unittest.TestCase):
    """Tests para MessageTemplate"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.template = MessageTemplate()

    def test_register_template(self):
        """Probar registración de plantilla"""
        self.template.register_template(
            "welcome",
            "Bienvenido {{name}}"
        )
        templates = self.template.list_templates()
        print(f"\n✓ Plantilla registrada")
        print(f"  Plantillas: {templates}")
        self.assertIn("welcome", templates)

    def test_render_template(self):
        """Probar renderización"""
        self.template.register_template(
            "promo",
            "Hola {{name}}, aprovecha {{discount}}% off"
        )
        result = self.template.render(
            "promo",
            {"name": "María", "discount": "30"}
        )
        print(f"\n✓ Plantilla renderizada")
        print(f"  Mensaje: {result['message']}")
        self.assertEqual(result["code"], 0)
        self.assertIn("María", result["message"])


class TestSMSQueue(unittest.TestCase):
    """Tests para SMSQueue"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.queue = SMSQueue(worker_count=1)

    def test_enqueue_sms(self):
        """Probar enqueuing de SMS"""
        task_id = self.queue.enqueue_sms(
            numbers=["3001234567"],
            content="Test",
            priority=SMSPriority.HIGH
        )
        print(f"\n✓ SMS encolado")
        print(f"  Task ID: {task_id}")
        self.assertIsNotNone(task_id)

    def test_get_status(self):
        """Probar estado de la cola"""
        self.queue.enqueue_sms(["3001234567"], "Test")
        status = self.queue.get_status()
        print(f"\n✓ Estado de cola: {status}")
        self.assertIn("queue_size", status)
        self.assertGreater(status["queue_size"], 0)

    def test_rate_limit(self):
        """Probar límite de velocidad"""
        self.queue.set_rate_limit(10)  # 10 SMS/segundo
        print(f"\n✓ Rate limit establecido: 10 SMS/s")
        self.assertEqual(self.queue.rate_limit, 10)

    def test_priority(self):
        """Probar prioridades"""
        task1 = SMSTask(
            id="task1",
            numbers=["3001234567"],
            content="Test1",
            priority=SMSPriority.LOW
        )
        task2 = SMSTask(
            id="task2",
            numbers=["3001234567"],
            content="Test2",
            priority=SMSPriority.URGENT
        )
        print(f"\n✓ Prioridades")
        print(f"  Task1 (LOW): {task1.priority.value}")
        print(f"  Task2 (URGENT): {task2.priority.value}")
        self.assertLess(task2.priority.value, task1.priority.value)


class TestSMSRetry(unittest.TestCase):
    """Tests para SMSRetry"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.retry = SMSRetry(max_retries=3)

    def test_add_to_queue(self):
        """Probar agregar a cola de reintentos"""
        self.retry.add_to_retry_queue(
            "SMS_001",
            ["3001234567"],
            "Test message"
        )
        print(f"\n✓ Agregado a cola de reintentos")
        status = self.retry.get_queue_status()
        print(f"  Queue size: {status['queue_size']}")
        self.assertEqual(status["queue_size"], 1)


def run_tests():
    """Ejecutar todos los tests"""
    # Crear suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestSMSSender))
    suite.addTests(loader.loadTestsFromTestCase(TestMessageProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestMessageTemplate))
    suite.addTests(loader.loadTestsFromTestCase(TestSMSQueue))
    suite.addTests(loader.loadTestsFromTestCase(TestSMSRetry))

    # Ejecutar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTS DE ENVÍO DE SMS")
    print("="*60)

    success = run_tests()

    print("\n" + "="*60)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")
