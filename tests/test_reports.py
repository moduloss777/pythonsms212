"""
Tests unitarios para módulos de reportes y análisis
Verifica generación de reportes, analytics y exportación
"""
import unittest
import sys
from pathlib import Path

# Agregar parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from report_generator import ReportGenerator, ErrorAnalyzer
from analytics import Analytics, ChartData
from exporters import CSVExporter, JSONExporter, TextExporter, ExportManager


class TestReportGenerator(unittest.TestCase):
    """Tests para ReportGenerator"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.gen = ReportGenerator()

    def test_generate_activity_summary(self):
        """Probar generación de resumen de actividad"""
        summary = self.gen.generate_activity_summary()
        print(f"\n✓ Resumen generado")
        print(f"  Campos: {list(summary.keys())}")
        self.assertIn("title", summary)
        self.assertIn("summary", summary)

    def test_generate_delivery_report(self):
        """Probar generación de reporte de entrega"""
        report = self.gen.generate_delivery_report()
        print(f"\n✓ Reporte de entrega generado")
        print(f"  Total: {report['summary']['total_reports']}")
        self.assertIn("summary", report)
        self.assertIn("delivery_rate", report['summary'])

    def test_compare_periods(self):
        """Probar comparación de períodos"""
        comparison = self.gen.compare_periods(7, 14)
        print(f"\n✓ Períodos comparados")
        print(f"  Tendencia: {comparison['comparison']['trend']}")
        self.assertIn("comparison", comparison)


class TestErrorAnalyzer(unittest.TestCase):
    """Tests para ErrorAnalyzer"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.analyzer = ErrorAnalyzer()

    def test_analyze_failures(self):
        """Probar análisis de fallos"""
        analysis = self.analyzer.analyze_failures()
        print(f"\n✓ Fallos analizados")
        print(f"  Total: {analysis['summary']['total_failures']}")
        self.assertIn("summary", analysis)

    def test_error_details(self):
        """Probar detalles de error"""
        details = self.analyzer.get_error_details(-1)
        print(f"\n✓ Detalles de error")
        print(f"  Error: {details['error_code']}")
        self.assertIn("description", details)
        self.assertIn("solutions", details)


class TestAnalytics(unittest.TestCase):
    """Tests para Analytics"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.analytics = Analytics()

    def test_calculate_kpis(self):
        """Probar cálculo de KPIs"""
        kpis = self.analytics.calculate_kpis()
        print(f"\n✓ KPIs calculados")
        print(f"  Tasa de envío: {kpis['sent_rate']:.2f}%")
        self.assertIn("delivery_rate", kpis)

    def test_get_hourly_distribution(self):
        """Probar distribución por hora"""
        hourly = self.analytics.get_hourly_distribution()
        print(f"\n✓ Distribución horaria")
        print(f"  Horas activas: {len(hourly)}")
        self.assertIsInstance(hourly, dict)

    def test_get_daily_distribution(self):
        """Probar distribución diaria"""
        daily = self.analytics.get_daily_distribution(days=7)
        print(f"\n✓ Distribución diaria")
        print(f"  Días: {len(daily)}")
        self.assertIsInstance(daily, dict)

    def test_get_top_operations(self):
        """Probar operaciones principales"""
        top = self.analytics.get_top_operations(limit=5)
        print(f"\n✓ Operaciones principales")
        print(f"  Cantidad: {len(top)}")
        self.assertIsInstance(top, list)

    def test_calculate_statistics(self):
        """Probar cálculo de estadísticas"""
        values = [1, 2, 3, 4, 5]
        stats = self.analytics.calculate_statistics(values)
        print(f"\n✓ Estadísticas calculadas")
        print(f"  Media: {stats['mean']}")
        self.assertIn("mean", stats)
        self.assertIn("median", stats)

    def test_generate_insights(self):
        """Probar generación de insights"""
        insights = self.analytics.generate_insights()
        print(f"\n✓ Insights generados")
        for insight in insights[:2]:
            print(f"  • {insight}")
        self.assertIsInstance(insights, list)


class TestChartData(unittest.TestCase):
    """Tests para ChartData"""

    def test_prepare_bar_chart(self):
        """Probar preparación de gráfico de barras"""
        data = {"A": 10, "B": 20, "C": 15}
        chart = ChartData.prepare_bar_chart(data)
        print(f"\n✓ Gráfico de barras preparado")
        self.assertEqual(chart["type"], "bar")
        self.assertEqual(len(chart["labels"]), 3)

    def test_prepare_pie_chart(self):
        """Probar preparación de gráfico de pastel"""
        data = {"Success": 80, "Failed": 20}
        chart = ChartData.prepare_pie_chart(data)
        print(f"\n✓ Gráfico de pastel preparado")
        self.assertEqual(chart["type"], "pie")
        self.assertIn("percentages", chart)


class TestExporters(unittest.TestCase):
    """Tests para exportadores"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.manager = ExportManager(output_dir="test_reports")

    def test_export_manager(self):
        """Probar gestor de exportación"""
        test_data = {
            "title": "Test",
            "summary": {"total": 100}
        }
        sms_list = [{"id": "1", "status": "sent"}]

        files = self.manager.export_complete(test_data, sms_list)
        print(f"\n✓ Exportación completa")
        print(f"  Archivos: {list(files.keys())}")
        self.assertIn("json", files)
        self.assertIn("csv", files)

    def test_json_export(self):
        """Probar exportación JSON"""
        data = {"test": "data"}
        file = self.manager.json_exporter.export_report(data, "test.json")
        print(f"\n✓ JSON exportado")
        self.assertTrue(file.endswith(".json"))

    def test_csv_export(self):
        """Probar exportación CSV"""
        data = [{"id": "1", "value": "test"}]
        file = self.manager.csv_exporter.export_sms_report(data, "test.csv")
        print(f"\n✓ CSV exportado")
        self.assertTrue(file.endswith(".csv"))


def run_tests():
    """Ejecutar todos los tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestReportGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalytics))
    suite.addTests(loader.loadTestsFromTestCase(TestChartData))
    suite.addTests(loader.loadTestsFromTestCase(TestExporters))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTS DE REPORTES Y ANÁLISIS")
    print("="*60)

    success = run_tests()

    print("\n" + "="*60)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")
