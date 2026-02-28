"""
Planificador automático de tareas
Ejecuta tareas en momentos específicos
"""
import logging
import time
import threading
from typing import Optional, Callable, Dict
from datetime import datetime, timedelta
from task_manager import TaskManager, TaskSchedule
from sms_sender import SMSSender

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Planificador de tareas automático"""

    def __init__(self, check_interval: int = 60):
        """
        Inicializar planificador

        Args:
            check_interval: Segundos entre verificaciones
        """
        self.manager = TaskManager()
        self.schedule_obj = TaskSchedule()
        self.sender = SMSSender()
        self.check_interval = check_interval
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.executed_tasks = []
        self.on_task_execute: Optional[Callable] = None

    def start(self):
        """Iniciar planificador"""
        if self.is_running:
            logger.warning("⚠️  Planificador ya está corriendo")
            return

        self.is_running = True
        logger.info(f"🚀 Iniciando planificador (intervalo: {self.check_interval}s)...")

        self.worker_thread = threading.Thread(
            target=self._scheduler_loop,
            name="TaskScheduler",
            daemon=True
        )
        self.worker_thread.start()

    def stop(self):
        """Detener planificador"""
        self.is_running = False
        logger.info("⏹️  Deteniendo planificador...")

        if self.worker_thread:
            self.worker_thread.join(timeout=5)

    def _scheduler_loop(self):
        """Loop principal del planificador"""
        logger.info("👷 Planificador iniciado")

        while self.is_running:
            try:
                # Construir calendario
                self.schedule_obj.build_schedule()

                # Obtener próxima tarea
                next_task = self.schedule_obj.get_next_task()

                if next_task:
                    # Verificar si es momento de ejecutar
                    task_id = next_task["task_id"]
                    task = self.manager.get_task(task_id)

                    if task and task["status"] == "active":
                        next_time = self.manager.get_next_execution_time(task_id)

                        if next_time and datetime.now() >= next_time:
                            logger.info(f"⏰ Ejecutando tarea: {task_id}")
                            self._execute_task(task_id, task)

                # Esperar antes de siguiente verificación
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Error en loop del planificador: {str(e)}")
                time.sleep(self.check_interval)

    def _execute_task(self, task_id: str, task: Dict):
        """
        Ejecutar una tarea

        Args:
            task_id: ID de la tarea
            task: Información de la tarea
        """
        try:
            logger.info(f"📤 Ejecutando: {task_id} ({task['type_name']})")

            # Enviar SMS
            result = self.sender.send_sms(
                numbers=task["contacts"],
                content=task["content"],
                sender=task["sender"],
                sendtime=task["sendtime"]
            )

            # Registrar ejecución
            self.executed_tasks.append({
                "task_id": task_id,
                "executed_at": datetime.now(),
                "result": result
            })

            # Actualizar contador en BD
            self.manager.db.execute_update(
                "UPDATE tasks SET executed_count = executed_count + 1 WHERE id = ?",
                (task_id,)
            )

            logger.info(f"✅ Tarea completada: {task_id} ({result.get('sms_count')} SMS)")

            # Llamar callback si existe
            if self.on_task_execute:
                self.on_task_execute(task_id, result)

            # Verificar si debe completarse
            if task["type"] == 1:  # Programada (una sola vez)
                self.manager.db.update_task_status(task_id, "completed")
                logger.info(f"✅ Tarea completada (tipo único): {task_id}")

        except Exception as e:
            logger.error(f"❌ Error ejecutando tarea: {str(e)}")

    def set_on_execute_callback(self, callback: Callable):
        """
        Configurar callback para ejecución

        Args:
            callback: Función a llamar después de ejecutar
        """
        self.on_task_execute = callback
        logger.info("✅ Callback configurado")

    def get_status(self) -> Dict:
        """
        Obtener estado del planificador

        Returns:
            Estado actual
        """
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "executed_count": len(self.executed_tasks),
            "scheduled_tasks": len(self.schedule_obj.schedule)
        }

    def get_execution_history(self, limit: int = 100) -> list:
        """
        Obtener histórico de ejecuciones

        Args:
            limit: Límite de registros

        Returns:
            Lista de ejecuciones
        """
        return self.executed_tasks[-limit:]

    def reschedule_task(self, task_id: str, new_sendtime: str) -> bool:
        """
        Reprogramar una tarea

        Args:
            task_id: ID de la tarea
            new_sendtime: Nuevo tiempo de envío

        Returns:
            True si fue reprogramada
        """
        logger.info(f"🔄 Reprogramando tarea: {task_id}")

        self.manager.db.execute_update(
            "UPDATE tasks SET sendtime = ? WHERE id = ?",
            (new_sendtime, task_id)
        )

        # Reconstruir calendario
        self.schedule_obj.build_schedule()

        return True


class CronExpressionParser:
    """Parser para expresiones cron simplificadas"""

    @staticmethod
    def parse_daily_at(hour: int, minute: int = 0) -> str:
        """
        Crear expresión para diaria a una hora específica

        Args:
            hour: Hora (0-23)
            minute: Minuto (0-59)

        Returns:
            Expresión en formato sendtime
        """
        now = datetime.now()
        scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if scheduled_time <= now:
            scheduled_time += timedelta(days=1)

        return scheduled_time.strftime("%Y%m%d%H%M%S")

    @staticmethod
    def parse_weekly_at(day_of_week: int, hour: int, minute: int = 0) -> str:
        """
        Crear expresión para semanal

        Args:
            day_of_week: Día de la semana (0=lunes, 6=domingo)
            hour: Hora
            minute: Minuto

        Returns:
            Expresión en formato sendtime
        """
        now = datetime.now()
        days_ahead = day_of_week - now.weekday()

        if days_ahead <= 0:
            days_ahead += 7

        scheduled_time = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

        return scheduled_time.strftime("%Y%m%d%H%M%S")

    @staticmethod
    def parse_monthly_at(day: int, hour: int, minute: int = 0) -> str:
        """
        Crear expresión para mensual

        Args:
            day: Día del mes (1-31)
            hour: Hora
            minute: Minuto

        Returns:
            Expresión en formato sendtime
        """
        now = datetime.now()

        try:
            scheduled_time = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)

            if scheduled_time <= now:
                # Ir al mes siguiente
                if now.month == 12:
                    scheduled_time = scheduled_time.replace(year=now.year + 1, month=1)
                else:
                    scheduled_time = scheduled_time.replace(month=now.month + 1)

        except ValueError:
            # Día inválido para este mes
            scheduled_time = now + timedelta(days=30)

        return scheduled_time.strftime("%Y%m%d%H%M%S")

    @staticmethod
    def parse_interval_hours(hours: int) -> str:
        """
        Crear expresión para intervalo en horas

        Args:
            hours: Número de horas

        Returns:
            Expresión en formato sendtime
        """
        scheduled_time = datetime.now() + timedelta(hours=hours)
        return scheduled_time.strftime("%Y%m%d%H%M%S")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL PLANIFICADOR")
    print("="*60 + "\n")

    scheduler = TaskScheduler(check_interval=5)

    print("1️⃣  Iniciando planificador...")
    scheduler.start()
    print("   ✅ Planificador iniciado\n")

    print("2️⃣  Estado del planificador...")
    status = scheduler.get_status()
    print(f"   {status}\n")

    print("3️⃣  Generando expresiones cron...")
    daily = CronExpressionParser.parse_daily_at(14, 30)
    print(f"   Diaria 14:30: {daily}")

    weekly = CronExpressionParser.parse_weekly_at(0, 9, 0)  # Lunes 09:00
    print(f"   Semanal lunes 09:00: {weekly}\n")

    # Esperar un poco
    print("4️⃣  Esperando verificaciones...")
    time.sleep(10)

    print("\n5️⃣  Deteniendo planificador...")
    scheduler.stop()
    print("   ✅ Planificador detenido\n")

    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
