"""
Generador de reportes para SMS y transacciones
Crea reportes detallados, resúmenes y análisis
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from database import Database
from config import ERROR_CODES

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generador de reportes"""

    def __init__(self):
        """Inicializar generador"""
        self.db = Database()

    def generate_sms_report(self, limit: int = 100) -> Dict:
        """
        Generar reporte de SMS

        Args:
            limit: Límite de SMS a incluir

        Returns:
            Reporte completo
        """
        logger.info(f"📊 Generando reporte de SMS (últimos {limit})...")

        sms_list = self.db.get_all_sms(limit=limit)

        total = len(sms_list)
        sent = sum(1 for s in sms_list if s['status'] == 'sent')
        failed = sum(1 for s in sms_list if s['status'] == 'failed')
        total_numbers = sum(len(s['numbers'].split(',')) for s in sms_list)

        report = {
            "title": "Reporte de SMS Enviados",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_sms": total,
                "sent": sent,
                "failed": failed,
                "success_rate": (sent / total * 100) if total > 0 else 0,
                "total_numbers": total_numbers
            },
            "details": sms_list
        }

        logger.info(f"✅ Reporte generado: {total} SMS, éxito: {report['summary']['success_rate']:.2f}%")
        return report

    def generate_delivery_report(self, sms_id: Optional[str] = None) -> Dict:
        """
        Generar reporte de entrega

        Args:
            sms_id: ID específico de SMS (si None, todos)

        Returns:
            Reporte de entrega
        """
        logger.info(f"📋 Generando reporte de entrega...")

        if sms_id:
            reports = self.db.get_reports_by_sms(sms_id)
        else:
            reports = self.db.execute_query("SELECT * FROM reports ORDER BY created_at DESC LIMIT 1000")

        delivered = sum(1 for r in reports if r['status'] == 'delivered')
        failed = sum(1 for r in reports if r['status'] == 'failed')
        total = len(reports)

        return {
            "title": "Reporte de Entrega",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_reports": total,
                "delivered": delivered,
                "failed": failed,
                "delivery_rate": (delivered / total * 100) if total > 0 else 0
            },
            "details": reports
        }

    def generate_transaction_report(self, days: int = 30) -> Dict:
        """
        Generar reporte de transacciones

        Args:
            days: Días a incluir

        Returns:
            Reporte de transacciones
        """
        logger.info(f"💰 Generando reporte de transacciones (últimos {days} días)...")

        transactions = self.db.get_transactions(limit=1000)

        total = len(transactions)
        successful = sum(1 for t in transactions if t['status'] == 'success')
        failed = sum(1 for t in transactions if t['status'] == 'failed')
        total_sms = sum(int(t['sms_count']) for t in transactions)

        return {
            "title": "Reporte de Transacciones",
            "generated_at": datetime.now().isoformat(),
            "period": f"Últimos {days} días",
            "summary": {
                "total_transactions": total,
                "successful": successful,
                "failed": failed,
                "total_sms_sent": total_sms,
                "success_rate": (successful / total * 100) if total > 0 else 0
            },
            "details": transactions
        }

    def generate_balance_history(self, account: str, days: int = 30) -> Dict:
        """
        Generar histórico de balance

        Args:
            account: Cuenta
            days: Días a incluir

        Returns:
            Histórico de balance
        """
        logger.info(f"💵 Generando histórico de balance para {account}...")

        history = self.db.get_balance_history(account, limit=1000)

        if not history:
            return {
                "account": account,
                "error": "No hay datos de balance"
            }

        first_balance = history[-1] if history else None
        last_balance = history[0] if history else None

        return {
            "title": "Histórico de Balance",
            "generated_at": datetime.now().isoformat(),
            "account": account,
            "summary": {
                "current_balance": last_balance['balance'] if last_balance else 0,
                "starting_balance": first_balance['balance'] if first_balance else 0,
                "change": (last_balance['balance'] - first_balance['balance']) if (first_balance and last_balance) else 0,
                "records": len(history)
            },
            "details": history
        }

    def generate_activity_summary(self) -> Dict:
        """
        Generar resumen de actividad

        Returns:
            Resumen general
        """
        logger.info("📈 Generando resumen de actividad...")

        stats = self.db.get_statistics()

        # Usar .get() con fallback para evitar KeyError
        total_sms = stats.get('total_sms', 0)
        sent_sms = stats.get('sent_sms', 0)
        delivered = stats.get('delivered_reports', 0)
        failed = total_sms - sent_sms

        return {
            "title": "Resumen de Actividad",
            "generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "summary": {
                "total_sms_messages": total_sms,
                "sent_messages": sent_sms,
                "failed_messages": failed,
                "total_delivered": delivered,
                "active_tasks": stats.get('active_tasks', 0),
                "total_transactions": stats.get('total_transactions', 0),
                # Agregar también estructura alternativa para compatibilidad
                "today": {
                    "sent": sent_sms,
                    "delivered": delivered,
                    "failed": failed
                }
            }
        }

    def compare_periods(self, period1_days: int = 7, period2_days: int = 14) -> Dict:
        """
        Comparar dos períodos

        Args:
            period1_days: Días del período 1 (más reciente)
            period2_days: Días del período 2 (más antiguo)

        Returns:
            Comparación de períodos
        """
        logger.info(f"📊 Comparando períodos: {period1_days} vs {period2_days} días...")

        now = datetime.now()
        period1_date = (now - timedelta(days=period1_days)).date()
        period2_date = (now - timedelta(days=period2_days)).date()

        # Obtener transacciones de cada período
        all_transactions = self.db.get_transactions(limit=10000)

        period1 = [t for t in all_transactions if
                  datetime.fromisoformat(t['created_at']).date() >= period1_date]
        period2 = [t for t in all_transactions if
                  datetime.fromisoformat(t['created_at']).date() >= period2_date and
                  datetime.fromisoformat(t['created_at']).date() < period1_date]

        p1_sms = sum(int(t['sms_count']) for t in period1)
        p2_sms = sum(int(t['sms_count']) for t in period2)

        growth = ((p1_sms - p2_sms) / p2_sms * 100) if p2_sms > 0 else 0

        return {
            "title": "Comparación de Períodos",
            "generated_at": datetime.now().isoformat(),
            "period1": {
                "days": period1_days,
                "transactions": len(period1),
                "sms_count": p1_sms
            },
            "period2": {
                "days": period2_days,
                "transactions": len(period2),
                "sms_count": p2_sms
            },
            "comparison": {
                "growth_percentage": growth,
                "sms_difference": p1_sms - p2_sms,
                "trend": "📈 Crecimiento" if growth > 0 else "📉 Decrecimiento" if growth < 0 else "➡️  Sin cambio"
            }
        }


class ErrorAnalyzer:
    """Analizador de errores"""

    def __init__(self):
        """Inicializar analizador"""
        self.db = Database()

    def analyze_failures(self, limit: int = 1000) -> Dict:
        """
        Analizar fallos

        Args:
            limit: Límite de reportes a analizar

        Returns:
            Análisis de errores
        """
        logger.info("🔍 Analizando fallos...")

        reports = self.db.execute_query(
            "SELECT * FROM reports WHERE status = 'failed' ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )

        error_codes = {}
        for report in reports:
            code = report.get('error_code')
            if code not in error_codes:
                error_codes[code] = 0
            error_codes[code] += 1

        total_failures = len(reports)

        return {
            "title": "Análisis de Fallos",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_failures": total_failures,
                "unique_error_codes": len(error_codes)
            },
            "error_distribution": {
                str(code): {
                    "count": count,
                    "percentage": (count / total_failures * 100) if total_failures > 0 else 0,
                    "description": ERROR_CODES.get(code, "Error desconocido")
                }
                for code, count in sorted(error_codes.items(), key=lambda x: x[1], reverse=True)
            }
        }

    def get_error_details(self, error_code: int) -> Dict:
        """
        Obtener detalles de un error específico

        Args:
            error_code: Código de error

        Returns:
            Detalles del error
        """
        return {
            "error_code": error_code,
            "description": ERROR_CODES.get(error_code, "Error desconocido"),
            "meaning": self._error_meaning(error_code),
            "solutions": self._error_solutions(error_code)
        }

    @staticmethod
    def _error_meaning(code: int) -> str:
        """Explicación detallada del error"""
        meanings = {
            -1: "Las credenciales (account/password) son inválidas",
            -2: "No se proporcionaron números de teléfono",
            -3: "El mensaje contiene caracteres sensibles no permitidos",
            -4: "El formato JSON de la solicitud es inválido",
            -5: "El mensaje es demasiado largo (máximo 1024 caracteres)",
            -6: "No se proporcionó contenido para el mensaje",
            -10: "No hay saldo suficiente en la cuenta",
        }
        return meanings.get(code, "Error no documentado")

    @staticmethod
    def _error_solutions(code: int) -> List[str]:
        """Soluciones sugeridas para cada error"""
        solutions = {
            -1: ["Verificar credenciales en config.py", "Contactar soporte de Traffilink"],
            -2: ["Proporcionar al menos un número de teléfono", "Validar formato de números"],
            -3: ["Remover caracteres especiales del mensaje", "Usar solo caracteres alfanuméricos"],
            -5: ["Dividir el mensaje en partes más pequeñas", "Reducir longitud del contenido"],
            -10: ["Agregar saldo a la cuenta", "Contactar con administrador para agregar crédito"],
        }
        return solutions.get(code, ["Contactar soporte técnico"])


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL GENERADOR DE REPORTES")
    print("="*60 + "\n")

    gen = ReportGenerator()
    analyzer = ErrorAnalyzer()

    print("1️⃣  Resumen de actividad...")
    summary = gen.generate_activity_summary()
    print(f"   {summary['summary']}\n")

    print("2️⃣  Análisis de fallos...")
    failures = analyzer.analyze_failures()
    print(f"   Fallos totales: {failures['summary']['total_failures']}\n")

    print("3️⃣  Detalles de error...")
    error_detail = analyzer.get_error_details(-1)
    print(f"   Error -1: {error_detail['description']}\n")

    gen.db.disconnect()

    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
