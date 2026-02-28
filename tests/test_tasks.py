"""
Tests unitarios para gestión de tareas
Verifica creación, ejecución y programación
"""
import unittest
import sys
import time
from pathlib import Path

# Agregar parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_manager import TaskManager, TaskSchedule
from scheduler import TaskScheduler, CronExpressionParser


class TestTaskManager(unittest.TestCase):
    """Tests para TaskManager"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.manager = TaskManager()

    def test_create_task(self):
        """Probar creación de tarea"""
        task_id = self.manager.create_task(
            task_type=0,
            contacts=["3001234567"],
            content="Test message"
        )
        print(f"\n✓ Tarea creada: {task_id}")
        self.assertIsNotNone(task_id)
        self.assertNotEqual(task_id, "")

    def test_get_task(self):
        """Probar obtener tarea"""
        task_id = self.manager.create_task(
            task_type=0,
            contacts=["3001234567"],
            content="Test"
        )
        task = self.manager.get_task(task_id)
        print(f"\n✓ Tarea obtenida: {task['type_name']}")
        self.assertIsNotNone(task)
        self.assertEqual(task["type"], 0)

    def test_list_active_tasks(self):
        """Probar listar tareas activas"""
        self.manager.create_task(0, ["3001234567"], "Test1")
        self.manager.create_task(0, ["3001234567"], "Test2")

        active = self.manager.get_active_tasks()
        print(f"\n✓ Tareas activas: {len(active)}")
        self.assertGreaterEqual(len(active), 2)

    def test_pause_task(self):
        """Probar pausar tarea"""
        task_id = self.manager.create_task(0, ["3001234567"], "Test")
        success = self.manager.pause_task(task_id)
        print(f"\n✓ Tarea pausada")
        self.assertTrue(success)

    def test_resume_task(self):
        """Probar reanudar tarea"""
        task_id = self.manager.create_task(0, ["3001234567"], "Test")
        self.manager.pause_task(task_id)
        success = self.manager.resume_task(task_id)
        print(f"\n✓ Tarea reanudada")
        self.assertTrue(success)

    def test_cancel_task(self):
        """Probar cancelar tarea"""
        task_id = self.manager.create_task(0, ["3001234567"], "Test")
        success = self.manager.cancel_task(task_id)
        print(f"\n✓ Tarea cancelada")
        self.assertTrue(success)

    def test_task_statistics(self):
        """Probar estadísticas de tareas"""
        self.manager.create_task(0, ["3001234567"], "Test1")
        self.manager.create_task(0, ["3001234567"], "Test2")

        stats = self.manager.get_task_statistics()
        print(f"\n✓ Estadísticas: {stats['total_tasks']} tareas")
        self.assertIn("total_tasks", stats)
        self.assertIn("active", stats)


class TestTaskSchedule(unittest.TestCase):
    """Tests para TaskSchedule"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.schedule = TaskSchedule()

    def test_build_schedule(self):
        """Probar construir calendario"""
        # Crear tarea
        self.schedule.manager.create_task(0, ["3001234567"], "Test")

        # Construir calendario
        calendar = self.schedule.build_schedule()
        print(f"\n✓ Calendario construido: {len(calendar)} fechas")
        self.assertIsInstance(calendar, dict)

    def test_get_next_task(self):
        """Probar obtener próxima tarea"""
        self.schedule.manager.create_task(0, ["3001234567"], "Test")
        self.schedule.build_schedule()

        next_task = self.schedule.get_next_task()
        print(f"\n✓ Próxima tarea: {next_task['type']}" if next_task else "Sin tareas")
        # next_task puede ser None si no hay tareas programadas


class TestTaskScheduler(unittest.TestCase):
    """Tests para TaskScheduler"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.scheduler = TaskScheduler(check_interval=2)

    def test_scheduler_start_stop(self):
        """Probar iniciar y detener planificador"""
        self.scheduler.start()
        print(f"\n✓ Planificador iniciado")

        status = self.scheduler.get_status()
        self.assertTrue(status["is_running"])

        self.scheduler.stop()
        print(f"✓ Planificador detenido")
        self.assertFalse(self.scheduler.is_running)

    def test_scheduler_status(self):
        """Probar estado del planificador"""
        status = self.scheduler.get_status()
        print(f"\n✓ Estado: is_running={status['is_running']}")
        self.assertIn("is_running", status)
        self.assertIn("check_interval", status)

    def test_execution_history(self):
        """Probar histórico de ejecuciones"""
        history = self.scheduler.get_execution_history()
        print(f"\n✓ Histórico: {len(history)} ejecuciones")
        self.assertIsInstance(history, list)

    def test_callback_configuration(self):
        """Probar configuración de callback"""
        def test_callback(task_id, result):
            pass

        self.scheduler.set_on_execute_callback(test_callback)
        print(f"\n✓ Callback configurado")
        self.assertIsNotNone(self.scheduler.on_task_execute)


class TestCronExpressionParser(unittest.TestCase):
    """Tests para CronExpressionParser"""

    def test_parse_daily(self):
        """Probar expresión diaria"""
        expr = CronExpressionParser.parse_daily_at(14, 30)
        print(f"\n✓ Diaria 14:30: {expr}")
        self.assertIsNotNone(expr)
        self.assertEqual(len(expr), 14)  # Formato YYYYMMDDHHmmss

    def test_parse_weekly(self):
        """Probar expresión semanal"""
        expr = CronExpressionParser.parse_weekly_at(0, 9, 0)  # Lunes 09:00
        print(f"\n✓ Semanal lunes 09:00: {expr}")
        self.assertIsNotNone(expr)

    def test_parse_monthly(self):
        """Probar expresión mensual"""
        expr = CronExpressionParser.parse_monthly_at(15, 10, 0)
        print(f"\n✓ Mensual día 15 10:00: {expr}")
        self.assertIsNotNone(expr)

    def test_parse_interval(self):
        """Probar expresión de intervalo"""
        expr = CronExpressionParser.parse_interval_hours(2)
        print(f"\n✓ Intervalo 2 horas: {expr}")
        self.assertIsNotNone(expr)


def run_tests():
    """Ejecutar todos los tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestTaskManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskSchedule))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestCronExpressionParser))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTS DE TAREAS PROGRAMADAS")
    print("="*60)

    success = run_tests()

    print("\n" + "="*60)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")
