"""
Sistema de cola para envío de SMS en background
Procesa SMS de forma asincrónica y controlada
"""
import logging
import time
from typing import List, Dict, Optional, Callable
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, PriorityQueue
import threading

logger = logging.getLogger(__name__)


class SMSPriority(Enum):
    """Prioridades de SMS"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


@dataclass
class SMSTask:
    """Tarea de SMS en la cola"""
    id: str
    numbers: List[str]
    content: str
    sender: Optional[str] = None
    sendtime: Optional[str] = None
    priority: SMSPriority = SMSPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, processing, completed, failed, retry
    attempts: int = 0
    max_attempts: int = 3
    result: Optional[Dict] = None

    def __lt__(self, other):
        """Comparación para priority queue"""
        return self.priority.value < other.priority.value

    def __str__(self):
        return (
            f"SMSTask(id={self.id}, status={self.status}, "
            f"numbers={len(self.numbers)}, attempts={self.attempts})"
        )


class SMSQueue:
    """Cola de envío de SMS"""

    def __init__(self, max_queue_size: int = 10000, worker_count: int = 1):
        """
        Inicializar cola

        Args:
            max_queue_size: Tamaño máximo de la cola
            worker_count: Número de workers
        """
        self.queue = PriorityQueue(maxsize=max_queue_size)
        self.processing_queue = {}
        self.completed_queue = []
        self.failed_queue = []
        self.worker_count = worker_count
        self.workers = []
        self.is_running = False
        self.send_callback: Optional[Callable] = None
        self.rate_limit = None  # SMS por segundo
        self.last_send_time = 0

    def set_send_callback(self, callback: Callable):
        """
        Configurar callback para enviar SMS

        Args:
            callback: Función que envía el SMS
        """
        self.send_callback = callback
        logger.info("✅ Callback de envío configurado")

    def enqueue(self, task: SMSTask) -> bool:
        """
        Agregar tarea a la cola

        Args:
            task: Tarea a agregar

        Returns:
            True si se agregó exitosamente
        """
        try:
            self.queue.put((task.priority.value, task.id, task), block=False)
            logger.info(f"📥 Tarea encolada: {task.id} (prioridad: {task.priority.name})")
            return True
        except Exception as e:
            logger.error(f"❌ Error enqueueing: {str(e)}")
            return False

    def enqueue_sms(self, numbers: List[str], content: str,
                   sender: Optional[str] = None, priority: SMSPriority = SMSPriority.NORMAL) -> str:
        """
        Crear y enqueuer tarea SMS

        Args:
            numbers: Números de teléfono
            content: Contenido
            sender: Remitente
            priority: Prioridad

        Returns:
            ID de la tarea
        """
        task = SMSTask(
            id=str(uuid4()),
            numbers=numbers,
            content=content,
            sender=sender,
            priority=priority
        )

        if self.enqueue(task):
            return task.id
        return ""

    def start(self):
        """Iniciar procesamiento de la cola"""
        if self.is_running:
            logger.warning("⚠️  Cola ya está corriendo")
            return

        self.is_running = True
        logger.info(f"🚀 Iniciando cola con {self.worker_count} workers...")

        for i in range(self.worker_count):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"SMSWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

    def stop(self):
        """Detener procesamiento"""
        self.is_running = False
        logger.info("⏹️  Deteniendo cola...")

        # Esperar a que terminen los workers
        for worker in self.workers:
            worker.join(timeout=5)

        logger.info("✅ Cola detenida")

    def _worker_loop(self):
        """Loop de procesamiento de worker"""
        logger.info(f"👷 Worker iniciado: {threading.current_thread().name}")

        while self.is_running:
            try:
                # Obtener tarea con timeout
                _, task_id, task = self.queue.get(timeout=1)

                # Aplicar rate limiting
                if self.rate_limit:
                    elapsed = time.time() - self.last_send_time
                    delay_needed = 1.0 / self.rate_limit
                    if elapsed < delay_needed:
                        time.sleep(delay_needed - elapsed)

                # Procesar tarea
                self._process_task(task)
                self.last_send_time = time.time()

            except Exception as e:
                logger.debug(f"Cola vacía o timeout: {str(e)}")

    def _process_task(self, task: SMSTask):
        """
        Procesar una tarea

        Args:
            task: Tarea a procesar
        """
        logger.info(f"⚙️  Procesando: {task.id}")

        task.status = "processing"
        task.started_at = datetime.now()
        task.attempts += 1

        self.processing_queue[task.id] = task

        try:
            if not self.send_callback:
                raise Exception("Callback de envío no configurado")

            # Llamar a la función de envío
            result = self.send_callback(
                numbers=task.numbers,
                content=task.content,
                sender=task.sender,
                sendtime=task.sendtime
            )

            task.result = result

            if result.get('code') == 0:
                task.status = "completed"
                self.completed_queue.append(task)
                logger.info(f"✅ Completado: {task.id}")
            else:
                raise Exception(result.get('error_message', 'Error desconocido'))

        except Exception as e:
            logger.error(f"❌ Error procesando {task.id}: {str(e)}")

            if task.attempts < task.max_attempts:
                task.status = "retry"
                logger.info(f"🔄 Reintentando {task.id} (intento {task.attempts + 1})")
                # Re-enqueuer
                self.enqueue(task)
            else:
                task.status = "failed"
                self.failed_queue.append(task)

        finally:
            task.completed_at = datetime.now()
            if task.id in self.processing_queue:
                del self.processing_queue[task.id]

    def set_rate_limit(self, sms_per_second: int):
        """
        Establecer límite de velocidad

        Args:
            sms_per_second: SMS por segundo
        """
        self.rate_limit = sms_per_second
        logger.info(f"⚡ Rate limit establecido: {sms_per_second} SMS/s")

    def get_status(self) -> Dict:
        """
        Obtener estado de la cola

        Returns:
            Dict con estadísticas
        """
        return {
            "queue_size": self.queue.qsize(),
            "processing": len(self.processing_queue),
            "completed": len(self.completed_queue),
            "failed": len(self.failed_queue),
            "is_running": self.is_running,
            "workers": self.worker_count
        }

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        Obtener estado de una tarea específica

        Args:
            task_id: ID de la tarea

        Returns:
            Estado de la tarea o None
        """
        # Buscar en procesamiento
        if task_id in self.processing_queue:
            task = self.processing_queue[task_id]
            return {
                "id": task.id,
                "status": task.status,
                "attempts": task.attempts,
                "started_at": task.started_at.isoformat() if task.started_at else None
            }

        # Buscar en completadas
        for task in self.completed_queue:
            if task.id == task_id:
                return {
                    "id": task.id,
                    "status": task.status,
                    "attempts": task.attempts,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": task.result
                }

        # Buscar en fallidas
        for task in self.failed_queue:
            if task.id == task_id:
                return {
                    "id": task.id,
                    "status": task.status,
                    "attempts": task.attempts,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": task.result
                }

        return None

    def get_completed_tasks(self, limit: int = 100) -> List[Dict]:
        """
        Obtener tareas completadas

        Args:
            limit: Límite de resultados

        Returns:
            Lista de tareas completadas
        """
        return [
            {
                "id": t.id,
                "status": t.status,
                "numbers": len(t.numbers),
                "attempts": t.attempts,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None
            }
            for t in self.completed_queue[-limit:]
        ]

    def get_failed_tasks(self, limit: int = 100) -> List[Dict]:
        """
        Obtener tareas fallidas

        Args:
            limit: Límite de resultados

        Returns:
            Lista de tareas fallidas
        """
        return [
            {
                "id": t.id,
                "status": t.status,
                "numbers": len(t.numbers),
                "attempts": t.attempts,
                "result": t.result
            }
            for t in self.failed_queue[-limit:]
        ]


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DE COLA SMS")
    print("="*60 + "\n")

    # Crear callback simulado
    def mock_send_sms(numbers, content, sender=None, sendtime=None):
        """Mock de envío"""
        time.sleep(0.1)  # Simular delay
        return {"code": 0, "id": str(uuid4())}

    # Crear cola
    queue = SMSQueue(worker_count=2)
    queue.set_send_callback(mock_send_sms)
    queue.set_rate_limit(5)  # 5 SMS/segundo

    # Iniciar
    queue.start()

    # Agregar tareas
    print("1️⃣  Agregando tareas a la cola...")
    for i in range(5):
        task_id = queue.enqueue_sms(
            numbers=["3001234567"],
            content=f"Mensaje {i+1}",
            priority=SMSPriority.NORMAL
        )
        print(f"   Tarea {i+1}: {task_id}")

    # Esperar procesamiento
    print("\n2️⃣  Esperando procesamiento...")
    time.sleep(3)

    # Estado
    print("\n3️⃣  Estado de la cola:")
    status = queue.get_status()
    print(f"   {status}")

    # Detener
    queue.stop()

    print("\n" + "="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
