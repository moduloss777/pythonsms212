"""
Gestor de tareas programadas para SMS
Crea, actualiza, ejecuta y monitorea tareas
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from database import Database
from config import TASK_TYPES

logger = logging.getLogger(__name__)


class TaskManager:
    """Gestor de tareas programadas"""

    def __init__(self):
        """Inicializar gestor"""
        self.db = Database()
        self.tasks = {}

    def create_task(self, task_type: int, contacts: List[str], content: str,
                   sender: Optional[str] = None, sendtime: Optional[str] = None,
                   interval: Optional[int] = None, endtime: Optional[str] = None) -> str:
        """
        Crear nueva tarea

        Args:
            task_type: Tipo de tarea (0-5)
            contacts: Lista de contactos
            content: Contenido del mensaje
            sender: Remitente opcional
            sendtime: Hora de envío
            interval: Intervalo en horas
            endtime: Hora de finalización

        Returns:
            ID de la tarea creada
        """
        task_id = str(uuid4())
        task_type_name = TASK_TYPES.get(task_type, "Desconocido")

        logger.info(f"📝 Creando tarea: {task_type_name} ({task_id})")

        # Guardar en BD
        success = self.db.save_task(
            task_id=task_id,
            account="0152C274",
            task_type=task_type,
            contacts=contacts,
            content=content,
            sender=sender,
            sendtime=sendtime,
            interval=interval,
            endtime=endtime
        )

        if success:
            # Almacenar en memoria también
            self.tasks[task_id] = {
                "id": task_id,
                "type": task_type,
                "type_name": task_type_name,
                "contacts": contacts,
                "content": content,
                "sender": sender,
                "sendtime": sendtime,
                "interval": interval,
                "endtime": endtime,
                "status": "active",
                "created_at": datetime.now(),
                "executed_count": 0
            }

            logger.info(f"✅ Tarea creada: {task_id}")
            return task_id
        else:
            logger.error(f"❌ Error creando tarea")
            return ""

    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Obtener información de una tarea

        Args:
            task_id: ID de la tarea

        Returns:
            Información de la tarea
        """
        if task_id in self.tasks:
            return self.tasks[task_id]

        # Buscar en BD
        task_data = self.db.execute_query(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        )

        if task_data:
            task = task_data[0]
            self.tasks[task_id] = {
                "id": task["id"],
                "type": task["task_type"],
                "type_name": TASK_TYPES.get(task["task_type"], "Desconocido"),
                "contacts": task["contacts"].split(","),
                "content": task["content"],
                "status": task["status"],
                "executed_count": task["executed_count"]
            }
            return self.tasks[task_id]

        return None

    def list_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """
        Listar tareas

        Args:
            status: Filtrar por estado (optional)

        Returns:
            Lista de tareas
        """
        tasks = self.db.execute_query(
            "SELECT * FROM tasks WHERE status = ? OR ? IS NULL ORDER BY created_at DESC",
            (status, status)
        )

        result = []
        for task in tasks:
            result.append({
                "id": task["id"],
                "type_name": TASK_TYPES.get(task["task_type"], "Desconocido"),
                "contacts_count": len(task["contacts"].split(",")),
                "status": task["status"],
                "executed": task["executed_count"]
            })

        return result

    def get_active_tasks(self) -> List[Dict]:
        """
        Obtener tareas activas

        Returns:
            Lista de tareas activas
        """
        return self.list_tasks(status="active")

    def pause_task(self, task_id: str) -> bool:
        """
        Pausar una tarea

        Args:
            task_id: ID de la tarea

        Returns:
            True si fue pausada
        """
        logger.info(f"⏸️  Pausando tarea: {task_id}")

        self.db.update_task_status(task_id, "paused")

        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "paused"

        return True

    def resume_task(self, task_id: str) -> bool:
        """
        Reanudar una tarea pausada

        Args:
            task_id: ID de la tarea

        Returns:
            True si fue reanudada
        """
        logger.info(f"▶️  Reanudando tarea: {task_id}")

        self.db.update_task_status(task_id, "active")

        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "active"

        return True

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancelar una tarea

        Args:
            task_id: ID de la tarea

        Returns:
            True si fue cancelada
        """
        logger.info(f"❌ Cancelando tarea: {task_id}")

        self.db.update_task_status(task_id, "cancelled")

        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "cancelled"

        return True

    def get_task_statistics(self) -> Dict:
        """
        Obtener estadísticas de tareas

        Returns:
            Estadísticas
        """
        tasks = self.db.execute_query("SELECT * FROM tasks")

        total = len(tasks)
        active = sum(1 for t in tasks if t["status"] == "active")
        paused = sum(1 for t in tasks if t["status"] == "paused")
        completed = sum(1 for t in tasks if t["status"] == "completed")
        cancelled = sum(1 for t in tasks if t["status"] == "cancelled")

        return {
            "total_tasks": total,
            "active": active,
            "paused": paused,
            "completed": completed,
            "cancelled": cancelled,
            "total_executions": sum(int(t["executed_count"]) for t in tasks)
        }

    def delete_task(self, task_id: str) -> bool:
        """
        Eliminar una tarea

        Args:
            task_id: ID de la tarea

        Returns:
            True si fue eliminada
        """
        logger.info(f"🗑️  Eliminando tarea: {task_id}")

        # En esta versión solo marcamos como eliminada
        self.db.update_task_status(task_id, "deleted")

        if task_id in self.tasks:
            del self.tasks[task_id]

        return True

    def get_next_execution_time(self, task_id: str) -> Optional[datetime]:
        """
        Calcular próximo tiempo de ejecución

        Args:
            task_id: ID de la tarea

        Returns:
            Datetime del próximo envío
        """
        task = self.get_task(task_id)
        if not task:
            return None

        task_type = task["type"]
        sendtime = task["sendtime"]

        if not sendtime:
            return None

        # Parsear sendtime (formato: YYYYMMDDHHMMSS)
        try:
            exec_time = datetime.strptime(sendtime, "%Y%m%d%H%M%S")
        except:
            return None

        now = datetime.now()

        if task_type == 0:  # Inmediata
            return now

        elif task_type == 1:  # Programada
            return exec_time if exec_time > now else None

        elif task_type == 2:  # Intervalo
            interval = task["interval"]
            if interval:
                return now + timedelta(hours=interval)

        elif task_type == 3:  # Diaria
            next_exec = exec_time.replace(day=now.day)
            if next_exec <= now:
                next_exec = next_exec + timedelta(days=1)
            return next_exec

        elif task_type == 4:  # Semanal
            next_exec = exec_time + timedelta(weeks=1)
            return next_exec

        elif task_type == 5:  # Mensual
            try:
                next_exec = exec_time.replace(month=(exec_time.month % 12) + 1)
            except:
                next_exec = exec_time + timedelta(days=30)
            return next_exec

        return None


class TaskSchedule:
    """Gestor de calendario de tareas"""

    def __init__(self):
        """Inicializar calendario"""
        self.manager = TaskManager()
        self.schedule = {}

    def build_schedule(self) -> Dict:
        """
        Construir calendario de próximas ejecuciones

        Returns:
            Calendario de tareas
        """
        logger.info("📅 Construyendo calendario de tareas...")

        tasks = self.manager.get_active_tasks()
        schedule = {}

        for task_summary in tasks:
            task = self.manager.get_task(task_summary["id"])
            if task:
                next_time = self.manager.get_next_execution_time(task_summary["id"])
                if next_time:
                    key = next_time.isoformat()
                    if key not in schedule:
                        schedule[key] = []
                    schedule[key].append({
                        "task_id": task_summary["id"],
                        "type": task["type_name"],
                        "contacts": len(task["contacts"])
                    })

        self.schedule = dict(sorted(schedule.items()))
        logger.info(f"✅ Calendario construido: {len(self.schedule)} días programados")
        return self.schedule

    def get_tasks_for_date(self, date: str) -> List[Dict]:
        """
        Obtener tareas para una fecha específica

        Args:
            date: Fecha en formato ISO

        Returns:
            Lista de tareas
        """
        return self.schedule.get(date, [])

    def get_next_task(self) -> Optional[Dict]:
        """
        Obtener próxima tarea a ejecutar

        Returns:
            Próxima tarea
        """
        if not self.schedule:
            self.build_schedule()

        if self.schedule:
            first_date = list(self.schedule.keys())[0]
            tasks = self.schedule[first_date]
            if tasks:
                return tasks[0]

        return None


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL GESTOR DE TAREAS")
    print("="*60 + "\n")

    manager = TaskManager()

    print("1️⃣  Creando tarea...")
    task_id = manager.create_task(
        task_type=0,  # Inmediata
        contacts=["3001234567"],
        content="Mensaje de prueba",
        sender="Test"
    )
    print(f"   Task ID: {task_id}\n")

    print("2️⃣  Listando tareas activas...")
    active = manager.get_active_tasks()
    print(f"   Total: {len(active)}\n")

    print("3️⃣  Estadísticas...")
    stats = manager.get_task_statistics()
    print(f"   {stats}\n")

    print("4️⃣  Construyendo calendario...")
    schedule = TaskSchedule()
    schedule.build_schedule()
    print(f"   Calendarios: {len(schedule.schedule)}\n")

    manager.db.disconnect()

    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
