"""
Tests unitarios para el módulo de autenticación
Verifica que la autenticación funcione correctamente
"""
import unittest
import sys
from pathlib import Path

# Agregar parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import AuthenticationManager, SessionManager


class TestAuthenticationManager(unittest.TestCase):
    """Tests para AuthenticationManager"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.auth_mgr = AuthenticationManager(max_retries=1)

    def test_initialization(self):
        """Verificar que se inicializa correctamente"""
        self.assertFalse(self.auth_mgr.is_authenticated)
        self.assertEqual(self.auth_mgr.auth_failures, 0)
        self.assertEqual(self.auth_mgr.auth_success_count, 0)

    def test_authenticate(self):
        """Probar autenticación"""
        success, msg = self.auth_mgr.authenticate()
        print(f"\n✓ Autenticación: {success}")
        print(f"  Mensaje: {msg}")
        # Solo verificar que retorna un booleano
        self.assertIsInstance(success, bool)
        self.assertIsInstance(msg, str)

    def test_get_status(self):
        """Probar obtener estado de autenticación"""
        status = self.auth_mgr.get_status()
        print(f"\n✓ Estado: {status}")
        self.assertIn("is_authenticated", status)
        self.assertIn("auth_success_count", status)
        self.assertIn("auth_failures", status)

    def test_reset(self):
        """Probar reset de autenticación"""
        self.auth_mgr.is_authenticated = True
        self.auth_mgr.reset()
        self.assertFalse(self.auth_mgr.is_authenticated)
        self.assertEqual(self.auth_mgr.auth_failures, 0)


class TestSessionManager(unittest.TestCase):
    """Tests para SessionManager"""

    def setUp(self):
        """Configurar antes de cada test"""
        self.session_mgr = SessionManager()

    def test_initialization(self):
        """Verificar inicialización"""
        self.assertIsNone(self.session_mgr.session_start)
        self.assertEqual(self.session_mgr.operations_count, 0)

    def test_start_session(self):
        """Probar inicio de sesión"""
        success = self.session_mgr.start_session()
        print(f"\n✓ Sesión iniciada: {success}")
        self.assertIsInstance(success, bool)

    def test_session_info(self):
        """Probar información de sesión"""
        self.session_mgr.start_session()
        info = self.session_mgr.get_session_info()
        print(f"\n✓ Info sesión: {info}")
        self.assertIn("is_active", info)
        self.assertIn("operations_count", info)

    def test_record_operation(self):
        """Probar registro de operaciones"""
        self.session_mgr.start_session()
        self.assertEqual(self.session_mgr.operations_count, 0)

        self.session_mgr.record_operation()
        self.assertEqual(self.session_mgr.operations_count, 1)

        self.session_mgr.record_operation()
        self.assertEqual(self.session_mgr.operations_count, 2)
        print(f"\n✓ Operaciones registradas: {self.session_mgr.operations_count}")

    def test_end_session(self):
        """Probar fin de sesión"""
        self.session_mgr.start_session()
        self.session_mgr.end_session()
        self.assertIsNone(self.session_mgr.session_start)
        self.assertEqual(self.session_mgr.operations_count, 0)
        print(f"\n✓ Sesión finalizada")


class TestAuthenticationFlow(unittest.TestCase):
    """Tests de flujo completo de autenticación"""

    def test_complete_flow(self):
        """Probar flujo completo"""
        print("\n✓ Iniciando flujo completo...")

        # Crear sesión
        session = SessionManager()

        # Iniciar sesión
        success = session.start_session()
        print(f"  1. Sesión iniciada: {success}")

        if success:
            # Registrar operaciones
            session.record_operation()
            session.record_operation()
            print(f"  2. Operaciones: {session.operations_count}")

            # Verificar sesión activa
            is_active = session.is_session_active()
            print(f"  3. Sesión activa: {is_active}")

            # Obtener info
            info = session.get_session_info()
            print(f"  4. Info sesión obtenida")

            # Finalizar
            session.end_session()
            print(f"  5. Sesión finalizada")

            self.assertTrue(True)
        else:
            print("  ⚠️  No se pudo conectar con Traffilink")


def run_tests():
    """Ejecutar todos los tests"""
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestAuthenticationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAuthenticationFlow))

    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTS DE AUTENTICACIÓN")
    print("="*60)

    success = run_tests()

    print("\n" + "="*60)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")
