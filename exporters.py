"""
Exportadores de reportes a diferentes formatos
CSV, Excel, PDF, JSON
"""
import logging
import json
import csv
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportExporter:
    """Exportador base de reportes"""

    def __init__(self, output_dir: str = "reports"):
        """
        Inicializar exportador

        Args:
            output_dir: Directorio de salida
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"📁 Directorio de reportes: {self.output_dir}")

    def generate_filename(self, report_name: str, extension: str) -> str:
        """
        Generar nombre de archivo con timestamp

        Args:
            report_name: Nombre del reporte
            extension: Extensión del archivo

        Returns:
            Nombre de archivo
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{report_name}_{timestamp}.{extension}"


class CSVExporter(ReportExporter):
    """Exportador a CSV"""

    def export_sms_report(self, data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Exportar reportes de SMS a CSV

        Args:
            data: Lista de diccionarios con datos de SMS
            filename: Nombre de archivo personalizado

        Returns:
            Ruta del archivo creado
        """
        if not data:
            logger.warning("⚠️  No hay datos para exportar")
            return ""

        filename = filename or self.generate_filename("sms_report", "csv")
        filepath = self.output_dir / filename

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"✅ Reporte CSV exportado: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ Error exportando CSV: {str(e)}")
            return ""

    def export_transactions(self, data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Exportar transacciones a CSV

        Args:
            data: Datos de transacciones
            filename: Nombre personalizado

        Returns:
            Ruta del archivo
        """
        return self.export_sms_report(data, filename or self.generate_filename("transactions", "csv"))


class JSONExporter(ReportExporter):
    """Exportador a JSON"""

    def export_report(self, data: Dict, filename: Optional[str] = None) -> str:
        """
        Exportar reporte completo a JSON

        Args:
            data: Datos del reporte
            filename: Nombre personalizado

        Returns:
            Ruta del archivo
        """
        filename = filename or self.generate_filename("report", "json")
        filepath = self.output_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"✅ Reporte JSON exportado: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ Error exportando JSON: {str(e)}")
            return ""

    def export_analytics(self, analytics: Dict, filename: Optional[str] = None) -> str:
        """
        Exportar análisis a JSON

        Args:
            analytics: Datos analíticos
            filename: Nombre personalizado

        Returns:
            Ruta del archivo
        """
        return self.export_report(analytics, filename or self.generate_filename("analytics", "json"))


class TextExporter(ReportExporter):
    """Exportador a texto plano"""

    def export_summary(self, summary: Dict, filename: Optional[str] = None) -> str:
        """
        Exportar resumen a texto plano

        Args:
            summary: Resumen del reporte
            filename: Nombre personalizado

        Returns:
            Ruta del archivo
        """
        filename = filename or self.generate_filename("summary", "txt")
        filepath = self.output_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._format_summary(summary))

            logger.info(f"✅ Resumen exportado: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ Error exportando TXT: {str(e)}")
            return ""

    @staticmethod
    def _format_summary(summary: Dict) -> str:
        """
        Formatear resumen para texto plano

        Args:
            summary: Diccionario de resumen

        Returns:
            Texto formateado
        """
        lines = []
        lines.append("=" * 60)
        lines.append("📊 REPORTE DE RESUMEN SMS")
        lines.append("=" * 60)
        lines.append("")

        if "title" in summary:
            lines.append(f"Título: {summary['title']}")

        if "generated_at" in summary:
            lines.append(f"Generado: {summary['generated_at']}")

        lines.append("")
        lines.append("RESUMEN:")
        lines.append("-" * 60)

        if "summary" in summary:
            for key, value in summary['summary'].items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, float):
                    lines.append(f"  {formatted_key}: {value:.2f}")
                else:
                    lines.append(f"  {formatted_key}: {value}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


class HTMLExporter(ReportExporter):
    """Exportador a HTML"""

    def export_dashboard(self, data: Dict, filename: Optional[str] = None) -> str:
        """
        Exportar dashboard a HTML

        Args:
            data: Datos del dashboard
            filename: Nombre personalizado

        Returns:
            Ruta del archivo
        """
        filename = filename or self.generate_filename("dashboard", "html")
        filepath = self.output_dir / filename

        try:
            html_content = self._generate_html(data)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"✅ Dashboard HTML exportado: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ Error exportando HTML: {str(e)}")
            return ""

    @staticmethod
    def _generate_html(data: Dict) -> str:
        """
        Generar HTML para dashboard

        Args:
            data: Datos

        Returns:
            Contenido HTML
        """
        html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte SMS - Goleador</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .card h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }
        .card .value {
            font-size: 28px;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #f0f0f0;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #999;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Reporte SMS - Goleador Marketing</h1>

        <div class="summary">
"""

        if "summary" in data:
            for key, value in data["summary"].items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, float):
                    display_value = f"{value:.2f}"
                else:
                    display_value = str(value)

                html += f"""
            <div class="card">
                <h3>{formatted_key}</h3>
                <div class="value">{display_value}</div>
            </div>
"""

        html += """
        </div>

        <div class="footer">
            <p>Generado: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </div>
    </div>
</body>
</html>
"""
        return html


class ExportManager:
    """Gestor centralizado de exportación"""

    def __init__(self, output_dir: str = "reports"):
        """
        Inicializar gestor

        Args:
            output_dir: Directorio de salida
        """
        self.csv_exporter = CSVExporter(output_dir)
        self.json_exporter = JSONExporter(output_dir)
        self.text_exporter = TextExporter(output_dir)
        self.html_exporter = HTMLExporter(output_dir)

    def export_complete(self, report_data: Dict, sms_list: List[Dict]) -> Dict:
        """
        Exportar reporte completo en todos los formatos

        Args:
            report_data: Datos del reporte
            sms_list: Lista de SMS

        Returns:
            Dict con rutas de archivos exportados
        """
        logger.info("📦 Exportando reporte completo...")

        files = {
            "json": self.json_exporter.export_report(report_data),
            "csv": self.csv_exporter.export_sms_report(sms_list),
            "txt": self.text_exporter.export_summary(report_data),
            "html": self.html_exporter.export_dashboard(report_data)
        }

        logger.info("✅ Exportación completa")
        return files


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DE EXPORTADORES")
    print("="*60 + "\n")

    manager = ExportManager()

    # Test CSV
    print("1️⃣  Exportando a CSV...")
    test_data = [
        {"id": "1", "status": "sent", "numbers": "3001234567"},
        {"id": "2", "status": "failed", "numbers": "3007654321"}
    ]
    csv_file = manager.csv_exporter.export_sms_report(test_data)
    print(f"   ✅ CSV: {csv_file}\n")

    # Test JSON
    print("2️⃣  Exportando a JSON...")
    json_file = manager.json_exporter.export_report({
        "title": "Test Report",
        "data": test_data
    })
    print(f"   ✅ JSON: {json_file}\n")

    # Test TXT
    print("3️⃣  Exportando a TXT...")
    txt_file = manager.text_exporter.export_summary({
        "title": "Test Summary",
        "summary": {"total": 2, "sent": 1, "failed": 1}
    })
    print(f"   ✅ TXT: {txt_file}\n")

    # Test HTML
    print("4️⃣  Exportando a HTML...")
    html_file = manager.html_exporter.export_dashboard({
        "summary": {"total": 100, "success_rate": 95.5}
    })
    print(f"   ✅ HTML: {html_file}\n")

    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
