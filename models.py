"""
Modelos de datos para el sistema de SMS
Define estructuras para SMS, Reportes, Tareas, etc.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SMSStatus(Enum):
    """Estados posibles de un SMS"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    UNDELIVERED = "undelivered"


class TaskType(Enum):
    """Tipos de tareas disponibles"""
    IMMEDIATE = 0
    SCHEDULED = 1
    INTERVAL = 2
    DAILY = 3
    WEEKLY = 4
    MONTHLY = 5


@dataclass
class SMS:
    """Modelo para un SMS"""
    id: str
    numbers: List[str]
    content: str
    status: SMSStatus = SMSStatus.PENDING
    sender: Optional[str] = None
    sendtime: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_count: int = 0
    failed_count: int = 0

    def __str__(self):
        return (
            f"SMS(id={self.id}, números={len(self.numbers)}, "
            f"estado={self.status.value}, entregados={self.delivered_count})"
        )


@dataclass
class Report:
    """Modelo para reporte de SMS"""
    id: str
    number: str
    status: SMSStatus
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    def __str__(self):
        return (
            f"Report(id={self.id}, número={self.number}, "
            f"estado={self.status.value})"
        )


@dataclass
class SMSTask:
    """Modelo para tarea de SMS programada"""
    id: str
    task_type: TaskType
    contacts: List[str]
    content: str
    sender: Optional[str] = None
    sendtime: Optional[str] = None
    interval: Optional[int] = None
    endtime: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"

    def __str__(self):
        return (
            f"Task(id={self.id}, tipo={self.task_type.name}, "
            f"contactos={len(self.contacts)}, estado={self.status})"
        )


@dataclass
class Account:
    """Modelo para información de cuenta"""
    account: str
    balance: float
    gift_balance: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def total_balance(self) -> float:
        """Obtener balance total (saldo + regalo)"""
        return self.balance + self.gift_balance

    def __str__(self):
        return (
            f"Account({self.account}) - "
            f"Balance: {self.balance}, Regalo: {self.gift_balance}, "
            f"Total: {self.total_balance}"
        )


@dataclass
class TransactionLog:
    """Modelo para registro de transacciones"""
    id: str
    operation: str  # "send_sms", "get_balance", etc.
    timestamp: datetime = field(default_factory=datetime.now)
    sms_count: int = 0
    balance_change: float = 0.0
    status: str = "success"
    notes: Optional[str] = None

    def __str__(self):
        return (
            f"Log(op={self.operation}, sms={self.sms_count}, "
            f"balance_change={self.balance_change}, estado={self.status})"
        )


class DataStorage:
    """Almacenamiento en memoria de datos (simplificado)"""

    def __init__(self):
        self.sms_messages: dict[str, SMS] = {}
        self.reports: dict[str, Report] = {}
        self.tasks: dict[str, SMSTask] = {}
        self.account: Optional[Account] = None
        self.transaction_logs: List[TransactionLog] = []

    def add_sms(self, sms: SMS):
        """Agregar SMS al almacenamiento"""
        self.sms_messages[sms.id] = sms

    def get_sms(self, sms_id: str) -> Optional[SMS]:
        """Obtener SMS por ID"""
        return self.sms_messages.get(sms_id)

    def add_report(self, report: Report):
        """Agregar reporte"""
        self.reports[report.id] = report

    def get_reports_by_sms_id(self, sms_id: str) -> List[Report]:
        """Obtener reportes de un SMS específico"""
        return [r for r in self.reports.values() if r.id.startswith(sms_id)]

    def add_task(self, task: SMSTask):
        """Agregar tarea"""
        self.tasks[task.id] = task

    def get_task(self, task_id: str) -> Optional[SMSTask]:
        """Obtener tarea por ID"""
        return self.tasks.get(task_id)

    def set_account(self, account: Account):
        """Actualizar información de cuenta"""
        self.account = account

    def log_transaction(self, log: TransactionLog):
        """Registrar transacción"""
        self.transaction_logs.append(log)

    def get_statistics(self) -> dict:
        """Obtener estadísticas generales"""
        total_sms = len(self.sms_messages)
        sent_sms = sum(1 for s in self.sms_messages.values()
                      if s.status == SMSStatus.SENT)
        failed_sms = sum(1 for s in self.sms_messages.values()
                        if s.status == SMSStatus.FAILED)
        delivered_count = sum(s.delivered_count for s in self.sms_messages.values())

        return {
            "total_sms_messages": total_sms,
            "sent_messages": sent_sms,
            "failed_messages": failed_sms,
            "total_delivered": delivered_count,
            "total_transactions": len(self.transaction_logs),
            "active_tasks": sum(1 for t in self.tasks.values()
                              if t.status == "active")
        }

    def __str__(self):
        stats = self.get_statistics()
        return (
            f"DataStorage("
            f"SMS={stats['total_sms_messages']}, "
            f"Enviados={stats['sent_messages']}, "
            f"Fallidos={stats['failed_messages']}, "
            f"Entregados={stats['total_delivered']}"
            f")"
        )
