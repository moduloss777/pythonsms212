"""
Tests para el dashboard web Flask
Verifica rutas, autenticación y funcionalidad de la API
"""
import unittest
import sys
import json
from pathlib import Path

# Agregar parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from database import Database


class TestWebRoutes(unittest.TestCase):
    """Tests para rutas web"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_login_page_get(self):
        """Probar carga de página de login"""
        response = self.client.get('/login')
        print(f"\n✓ Login page GET: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

    def test_login_invalid_credentials(self):
        """Probar login con credenciales inválidas"""
        response = self.client.post('/login', data={
            'account': 'invalid',
            'password': 'invalid'
        }, follow_redirects=True)
        print(f"✓ Invalid login: {response.status_code}")
        self.assertIn(b'login', response.data.lower())

    def test_dashboard_requires_login(self):
        """Probar que dashboard requiere login"""
        response = self.client.get('/dashboard')
        print(f"✓ Dashboard redirect without login: {response.status_code}")
        # Debería redirigir a login o retornar 401
        self.assertIn(response.status_code, [302, 401])

    def test_api_dashboard_stats(self):
        """Probar endpoint de estadísticas del dashboard"""
        response = self.client.get('/api/dashboard/stats')
        print(f"✓ Dashboard stats API: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('total_sent', data)
            self.assertIn('success_rate', data)

    def test_api_balance(self):
        """Probar endpoint de balance"""
        response = self.client.get('/api/dashboard/balance')
        print(f"✓ Balance API: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('balance', data)

    def test_api_hourly_distribution(self):
        """Probar endpoint de distribución horaria"""
        response = self.client.get('/api/dashboard/hourly')
        print(f"✓ Hourly distribution API: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('hours', data)
            self.assertIn('counts', data)

    def test_api_insights(self):
        """Probar endpoint de insights"""
        response = self.client.get('/api/dashboard/insights')
        print(f"✓ Insights API: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('insights', data)

    def test_sms_send_invalid_data(self):
        """Probar envío de SMS sin datos"""
        response = self.client.post('/api/sms/send',
            json={},
            content_type='application/json'
        )
        print(f"✓ SMS send invalid: {response.status_code}")
        self.assertIn(response.status_code, [400, 401])

    def test_sms_history(self):
        """Probar historial de SMS"""
        response = self.client.get('/api/sms/history')
        print(f"✓ SMS history API: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('sms_list', data)

    def test_reports_sms(self):
        """Probar reporte de SMS"""
        response = self.client.get('/api/reports/sms')
        print(f"✓ SMS report API: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('rows', data)

    def test_reports_delivery(self):
        """Probar reporte de entrega"""
        response = self.client.get('/api/reports/delivery')
        print(f"✓ Delivery report API: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('rows', data)

    def test_reports_transactions(self):
        """Probar reporte de transacciones"""
        response = self.client.get('/api/reports/transactions')
        print(f"✓ Transactions report API: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('rows', data)

    def test_tasks_list(self):
        """Probar listado de tareas"""
        response = self.client.get('/api/tasks/list')
        print(f"✓ Tasks list API: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('tasks', data)

    def test_tasks_create_invalid(self):
        """Probar creación de tarea sin datos"""
        response = self.client.post('/api/tasks/create',
            json={},
            content_type='application/json'
        )
        print(f"✓ Tasks create invalid: {response.status_code}")
        self.assertIn(response.status_code, [400, 401])

    def test_404_not_found(self):
        """Probar página no encontrada"""
        response = self.client.get('/invalid-page')
        print(f"✓ 404 Not Found: {response.status_code}")
        self.assertEqual(response.status_code, 404)

    def test_logout(self):
        """Probar logout"""
        response = self.client.get('/logout', follow_redirects=True)
        print(f"✓ Logout: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])


class TestAPIValidation(unittest.TestCase):
    """Tests para validación de API"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.app = app
        self.client = self.app.test_client()

    def test_json_content_type_required(self):
        """Probar que endpoints POST requieren JSON"""
        response = self.client.post('/api/sms/send',
            data='invalid',
            content_type='text/plain'
        )
        print(f"\n✓ JSON content type validation: {response.status_code}")
        # Debería rechazar o procesar como error
        self.assertIn(response.status_code, [400, 401, 415])

    def test_empty_sms_content(self):
        """Probar SMS con contenido vacío"""
        response = self.client.post('/api/sms/send',
            json={
                'numbers': ['3001234567'],
                'content': ''
            },
            content_type='application/json'
        )
        print(f"✓ Empty SMS content: {response.status_code}")
        self.assertIn(response.status_code, [400, 401])

    def test_invalid_phone_numbers(self):
        """Probar SMS con números inválidos"""
        response = self.client.post('/api/sms/send',
            json={
                'numbers': ['invalid'],
                'content': 'Test'
            },
            content_type='application/json'
        )
        print(f"✓ Invalid phone numbers: {response.status_code}")
        self.assertIn(response.status_code, [400, 401])

    def test_response_json_format(self):
        """Probar formato JSON de respuestas"""
        response = self.client.get('/api/dashboard/stats')

        if response.status_code == 200:
            try:
                data = json.loads(response.data)
                print(f"✓ JSON format valid")
                self.assertIsInstance(data, dict)
            except json.JSONDecodeError:
                print(f"✗ Invalid JSON response")
                self.fail("Response is not valid JSON")

    def test_api_error_responses(self):
        """Probar respuestas de error de API"""
        # Intentar acceder con método no permitido
        response = self.client.post('/api/dashboard/stats')
        print(f"✓ API error response: {response.status_code}")
        # POST no está permitido en GET endpoints
        self.assertIn(response.status_code, [405, 401])


class TestWebIntegration(unittest.TestCase):
    """Tests de integración web"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.app = app
        self.client = self.app.test_client()
        self.db = Database()

    def test_dashboard_displays_stats(self):
        """Probar que dashboard muestra estadísticas"""
        response = self.client.get('/api/dashboard/stats')
        print(f"\n✓ Dashboard stats loading")

        if response.status_code == 200:
            data = json.loads(response.data)
            # Verificar que tiene campos esperados
            expected_fields = ['total_sent', 'success_rate', 'balance', 'active_tasks']
            for field in expected_fields:
                self.assertIn(field, data, f"Missing field: {field}")

    def test_chart_data_consistency(self):
        """Probar consistencia de datos de gráficos"""
        response = self.client.get('/api/dashboard/hourly')
        print(f"✓ Chart data consistency")

        if response.status_code == 200:
            data = json.loads(response.data)
            # Las horas y conteos deben tener la misma longitud
            if 'hours' in data and 'counts' in data:
                self.assertEqual(len(data['hours']), len(data['counts']))

    def test_report_data_structure(self):
        """Probar estructura de datos de reportes"""
        response = self.client.get('/api/reports/sms')
        print(f"✓ Report data structure")

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('rows', data)
            self.assertIsInstance(data['rows'], list)

    def tearDown(self):
        """Limpiar después de cada test"""
        if hasattr(self, 'db'):
            self.db.disconnect()


def run_tests():
    """Ejecutar todos los tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestWebRoutes))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestWebIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTS DEL DASHBOARD WEB")
    print("="*60)

    success = run_tests()

    print("\n" + "="*60)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")
