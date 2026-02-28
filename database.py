"""
Capa de persistencia usando SQLite
Almacena SMS, reportes, transacciones y metadatos
"""
import sqlite3
import logging
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Ruta de base de datos
DB_PATH = Path("traffilink.db")


class Database:
    """Gestor de base de datos SQLite"""

    def __init__(self, db_path: str = str(DB_PATH)):
        """
        Inicializar conexión a base de datos

        Args:
            db_path: Ruta del archivo de base de datos
        """
        self.db_path = db_path
        self.connection = None
        self.init_database()

    def connect(self):
        """Conectar a la base de datos"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"✅ Conectado a base de datos: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"❌ Error de conexión a BD: {str(e)}")
            raise

    def disconnect(self):
        """Desconectar de la base de datos"""
        if self.connection:
            self.connection.close()
            logger.info("👋 Desconectado de base de datos")

    def init_database(self):
        """Inicializar tablas si no existen"""
        self.connect()

        cursor = self.connection.cursor()

        # Tabla de SMS enviados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sms (
                id TEXT PRIMARY KEY,
                account TEXT NOT NULL,
                numbers TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                sender TEXT,
                sendtime TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0
            )
        """)

        # Tabla de reportes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                sms_id TEXT NOT NULL,
                number TEXT NOT NULL,
                status TEXT NOT NULL,
                error_code INTEGER,
                error_message TEXT,
                sent_at TIMESTAMP,
                delivered_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(sms_id) REFERENCES sms(id)
            )
        """)

        # Tabla de tareas programadas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                account TEXT NOT NULL,
                task_type INTEGER NOT NULL,
                contacts TEXT NOT NULL,
                content TEXT NOT NULL,
                sender TEXT,
                sendtime TEXT,
                interval INTEGER,
                endtime TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_count INTEGER DEFAULT 0
            )
        """)

        # Tabla de transacciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                sms_count INTEGER DEFAULT 0,
                balance_change REAL DEFAULT 0,
                status TEXT DEFAULT 'success',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de balance histórico
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS balance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account TEXT NOT NULL,
                balance REAL NOT NULL,
                gift_balance REAL DEFAULT 0,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()
        logger.info("✅ Base de datos inicializada")

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """
        Ejecutar consulta SELECT

        Args:
            query: Consulta SQL
            params: Parámetros

        Returns:
            Lista de resultados como dicts
        """
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Ejecutar INSERT, UPDATE o DELETE

        Args:
            query: Consulta SQL
            params: Parámetros

        Returns:
            Número de filas afectadas
        """
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor.rowcount

    # ==================== SMS ====================

    def save_sms(self, sms_id: str, account: str, numbers: List[str],
                 content: str, sender: Optional[str] = None,
                 sendtime: Optional[str] = None) -> bool:
        """Guardar SMS enviado"""
        try:
            query = """
                INSERT INTO sms (id, account, numbers, content, sender, sendtime, status)
                VALUES (?, ?, ?, ?, ?, ?, 'sent')
            """
            numbers_str = ",".join(numbers) if isinstance(numbers, list) else numbers
            self.execute_update(query, (sms_id, account, numbers_str, content, sender, sendtime))
            logger.info(f"💾 SMS guardado: {sms_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando SMS: {str(e)}")
            return False

    def get_sms(self, sms_id: str) -> Optional[Dict]:
        """Obtener SMS por ID"""
        query = "SELECT * FROM sms WHERE id = ?"
        results = self.execute_query(query, (sms_id,))
        return results[0] if results else None

    def get_all_sms(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Obtener todos los SMS"""
        query = "SELECT * FROM sms ORDER BY sent_at DESC LIMIT ? OFFSET ?"
        return self.execute_query(query, (limit, offset))

    def update_sms_status(self, sms_id: str, status: str,
                         delivered: int = 0, failed: int = 0):
        """Actualizar estado de SMS"""
        query = """
            UPDATE sms
            SET status = ?, delivered_count = ?, failed_count = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        self.execute_update(query, (status, delivered, failed, sms_id))

    # ==================== REPORTES ====================

    def save_report(self, report_id: str, sms_id: str, number: str,
                   status: str, error_code: Optional[int] = None,
                   error_message: Optional[str] = None) -> bool:
        """Guardar reporte de entrega"""
        try:
            query = """
                INSERT INTO reports (id, sms_id, number, status, error_code, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.execute_update(query, (report_id, sms_id, number, status, error_code, error_message))
            logger.info(f"📋 Reporte guardado: {report_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando reporte: {str(e)}")
            return False

    def get_reports_by_sms(self, sms_id: str) -> List[Dict]:
        """Obtener reportes de un SMS"""
        query = "SELECT * FROM reports WHERE sms_id = ? ORDER BY created_at DESC"
        return self.execute_query(query, (sms_id,))

    # ==================== TAREAS ====================

    def save_task(self, task_id: str, account: str, task_type: int,
                 contacts: List[str], content: str, sender: Optional[str] = None,
                 sendtime: Optional[str] = None, interval: Optional[int] = None,
                 endtime: Optional[str] = None) -> bool:
        """Guardar tarea programada"""
        try:
            query = """
                INSERT INTO tasks (id, account, task_type, contacts, content, sender, sendtime, interval, endtime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            contacts_str = ",".join(contacts) if isinstance(contacts, list) else contacts
            self.execute_update(query, (task_id, account, task_type, contacts_str, content,
                                       sender, sendtime, interval, endtime))
            logger.info(f"⏰ Tarea guardada: {task_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando tarea: {str(e)}")
            return False

    def get_active_tasks(self) -> List[Dict]:
        """Obtener tareas activas"""
        query = "SELECT * FROM tasks WHERE status = 'active' ORDER BY created_at DESC"
        return self.execute_query(query)

    def update_task_status(self, task_id: str, status: str):
        """Actualizar estado de tarea"""
        query = "UPDATE tasks SET status = ? WHERE id = ?"
        self.execute_update(query, (status, task_id))

    # ==================== TRANSACCIONES ====================

    def save_transaction(self, transaction_id: str, operation: str,
                        sms_count: int = 0, balance_change: float = 0,
                        status: str = "success", notes: Optional[str] = None) -> bool:
        """Guardar transacción"""
        try:
            query = """
                INSERT INTO transactions (id, operation, sms_count, balance_change, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.execute_update(query, (transaction_id, operation, sms_count, balance_change, status, notes))
            logger.info(f"📊 Transacción guardada: {transaction_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando transacción: {str(e)}")
            return False

    def get_transactions(self, limit: int = 100) -> List[Dict]:
        """Obtener últimas transacciones"""
        query = "SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?"
        return self.execute_query(query, (limit,))

    # ==================== BALANCE ====================

    def save_balance(self, account: str, balance: float, gift_balance: float = 0):
        """Guardar balance en histórico"""
        query = """
            INSERT INTO balance_history (account, balance, gift_balance)
            VALUES (?, ?, ?)
        """
        self.execute_update(query, (account, balance, gift_balance))
        logger.debug(f"💰 Balance histórico guardado: {account} - ${balance}")

    def get_balance_history(self, account: str, limit: int = 100) -> List[Dict]:
        """Obtener histórico de balance"""
        query = """
            SELECT * FROM balance_history
            WHERE account = ?
            ORDER BY recorded_at DESC
            LIMIT ?
        """
        return self.execute_query(query, (account, limit))

    # ==================== ESTADÍSTICAS ====================

    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas generales"""
        stats = {}

        # Total de SMS
        result = self.execute_query("SELECT COUNT(*) as count FROM sms")
        stats["total_sms"] = result[0]["count"] if result else 0

        # SMS enviados
        result = self.execute_query("SELECT COUNT(*) as count FROM sms WHERE status = 'sent'")
        stats["sent_sms"] = result[0]["count"] if result else 0

        # Total de reportes
        result = self.execute_query("SELECT COUNT(*) as count FROM reports")
        stats["total_reports"] = result[0]["count"] if result else 0

        # Reportes entregados
        result = self.execute_query("SELECT COUNT(*) as count FROM reports WHERE status = 'delivered'")
        stats["delivered_reports"] = result[0]["count"] if result else 0

        # Tareas activas
        result = self.execute_query("SELECT COUNT(*) as count FROM tasks WHERE status = 'active'")
        stats["active_tasks"] = result[0]["count"] if result else 0

        # Total de transacciones
        result = self.execute_query("SELECT COUNT(*) as count FROM transactions")
        stats["total_transactions"] = result[0]["count"] if result else 0

        return stats

    def cleanup_old_data(self, days: int = 30) -> int:
        """
        Limpiar datos antiguos

        Args:
            days: Días a mantener

        Returns:
            Número de registros eliminados
        """
        date_limit = f"{datetime.now().year}-{(datetime.now().month - 1):02d}-{datetime.now().day:02d}"

        # Limpiar SMS antiguo
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM sms WHERE date(sent_at) < date(?)", (date_limit,))
        sms_count = cursor.rowcount

        # Limpiar reportes antiguos
        cursor.execute("DELETE FROM reports WHERE date(created_at) < date(?)", (date_limit,))
        reports_count = cursor.rowcount

        self.connection.commit()

        total = sms_count + reports_count
        logger.info(f"🧹 Datos antiguos limpiados: {total} registros")
        return total


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DE BASE DE DATOS")
    print("="*60 + "\n")

    db = Database("test_traffilink.db")

    print("1️⃣  Guardando SMS...")
    db.save_sms("SMS_001", "0152C274", ["3001234567", "3007654321"],
               "Mensaje de prueba", sender="Test")

    print("2️⃣  Obteniendo SMS...")
    sms = db.get_sms("SMS_001")
    print(f"   SMS: {sms}\n")

    print("3️⃣  Guardando reporte...")
    db.save_report("REP_001", "SMS_001", "3001234567", "delivered")

    print("4️⃣  Obteniendo reportes...")
    reports = db.get_reports_by_sms("SMS_001")
    print(f"   Reportes: {reports}\n")

    print("5️⃣  Guardando balance histórico...")
    db.save_balance("0152C274", 1000.50, 50.00)

    print("6️⃣  Estadísticas...")
    stats = db.get_statistics()
    print(f"   {stats}\n")

    db.disconnect()

    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
