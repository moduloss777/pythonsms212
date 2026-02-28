"""
Gestor avanzado de autenticación para Traffilink API
Maneja validación, reintentos, y caching de estado de autenticación
"""
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from traffilink_api import TrafficLinkAPI
from config import TRAFFILINK_ACCOUNT, TRAFFILINK_PASSWORD

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Gestor centralizado de autenticación"""

    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Inicializar gestor de autenticación

        Args:
            max_retries: Máximo número de reintentos
            retry_delay: Segundos entre reintentos
        """
        self.api = TrafficLinkAPI(
            account=TRAFFILINK_ACCOUNT,
            password=TRAFFILINK_PASSWORD
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.is_authenticated = False
        self.last_auth_time: Optional[datetime] = None
        self.auth_failures = 0
        self.auth_success_count = 0

    def authenticate(self) -> Tuple[bool, str]:
        """
        Autenticar contra Traffilink API

        Returns:
            Tupla (es_autenticado, mensaje)
        """
        logger.info("🔐 Intentando autenticación con Traffilink...")

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.api.get_balance()

                if response.get('code') == 0:
                    self.is_authenticated = True
                    self.last_auth_time = datetime.now()
                    self.auth_success_count += 1
                    self.auth_failures = 0

                    msg = f"✅ Autenticado exitosamente (intento {attempt})"
                    logger.info(msg)
                    return True, msg

                elif response.get('code') == -1:
                    error_msg = "❌ Credenciales inválidas"
                    logger.error(error_msg)
                    self.is_authenticated = False
                    self.auth_failures += 1
                    return False, error_msg

            except Exception as e:
                logger.warning(f"⚠️  Intento {attempt} falló: {str(e)}")

                if attempt < self.max_retries:
                    import time
                    time.sleep(self.retry_delay)
                else:
                    error_msg = f"❌ Autenticación fallida después de {self.max_retries} intentos"
                    logger.error(error_msg)
                    self.is_authenticated = False
                    self.auth_failures += 1
                    return False, error_msg

        return False, "❌ Autenticación fallida"

    def is_authenticated_cached(self, cache_duration: int = 300) -> bool:
        """
        Verificar si está autenticado (usando caché)

        Args:
            cache_duration: Segundos antes de reintentar autenticación

        Returns:
            True si está autenticado y caché es válido
        """
        if not self.is_authenticated:
            return False

        if self.last_auth_time is None:
            return False

        elapsed = (datetime.now() - self.last_auth_time).total_seconds()

        if elapsed > cache_duration:
            logger.info("🔄 Caché de autenticación expirado, reautenticando...")
            return self.authenticate()[0]

        return True

    def require_authentication(self) -> bool:
        """
        Requerir autenticación válida (reintentar si es necesario)

        Returns:
            True si está autenticado, False si no
        """
        if self.is_authenticated_cached():
            return True

        success, msg = self.authenticate()
        return success

    def get_status(self) -> Dict:
        """
        Obtener estado actual de autenticación

        Returns:
            Dict con información de estado
        """
        return {
            "is_authenticated": self.is_authenticated,
            "last_auth_time": self.last_auth_time.isoformat() if self.last_auth_time else None,
            "auth_success_count": self.auth_success_count,
            "auth_failures": self.auth_failures,
            "account": TRAFFILINK_ACCOUNT
        }

    def reset(self):
        """Resetear estado de autenticación"""
        self.is_authenticated = False
        self.last_auth_time = None
        self.auth_failures = 0
        logger.info("🔄 Estado de autenticación reseteado")


class SessionManager:
    """Gestor de sesiones de usuario"""

    def __init__(self):
        self.auth_manager = AuthenticationManager()
        self.session_start: Optional[datetime] = None
        self.operations_count = 0
        self.last_operation: Optional[datetime] = None

    def start_session(self) -> bool:
        """
        Iniciar nueva sesión

        Returns:
            True si la sesión se inició exitosamente
        """
        logger.info("🚀 Iniciando nueva sesión...")

        success, msg = self.auth_manager.authenticate()

        if success:
            self.session_start = datetime.now()
            self.operations_count = 0
            logger.info("✅ Sesión iniciada")
            return True
        else:
            logger.error(f"❌ No se pudo iniciar sesión: {msg}")
            return False

    def is_session_active(self, session_timeout: int = 3600) -> bool:
        """
        Verificar si la sesión está activa

        Args:
            session_timeout: Segundos antes de que expire la sesión

        Returns:
            True si la sesión está activa
        """
        if self.session_start is None:
            return False

        elapsed = (datetime.now() - self.session_start).total_seconds()

        if elapsed > session_timeout:
            logger.warning("⚠️  Sesión expirada")
            return False

        return self.auth_manager.is_authenticated_cached()

    def end_session(self):
        """Terminar sesión actual"""
        logger.info(f"👋 Sesión finalizada - {self.operations_count} operaciones")
        self.session_start = None
        self.operations_count = 0
        self.auth_manager.reset()

    def get_session_info(self) -> Dict:
        """
        Obtener información de la sesión

        Returns:
            Dict con detalles de la sesión
        """
        return {
            "session_start": self.session_start.isoformat() if self.session_start else None,
            "is_active": self.is_session_active(),
            "operations_count": self.operations_count,
            "last_operation": self.last_operation.isoformat() if self.last_operation else None,
            "auth_status": self.auth_manager.get_status()
        }

    def record_operation(self):
        """Registrar operación en la sesión"""
        self.operations_count += 1
        self.last_operation = datetime.now()


class AuthDecorator:
    """Decorador para requerir autenticación en métodos"""

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def require_session(self, func):
        """Decorador que requiere sesión activa"""
        def wrapper(*args, **kwargs):
            if not self.session_manager.is_session_active():
                logger.error("❌ Sesión no activa")
                return {"code": -999, "error_message": "Sesión no activa"}

            self.session_manager.record_operation()
            return func(*args, **kwargs)

        return wrapper


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL GESTOR DE AUTENTICACIÓN")
    print("="*60 + "\n")

    # Test 1: AuthenticationManager
    print("1️⃣  Probando AuthenticationManager...")
    auth_mgr = AuthenticationManager()
    success, msg = auth_mgr.authenticate()
    print(f"   Resultado: {msg}")
    print(f"   Estado: {auth_mgr.get_status()}\n")

    # Test 2: SessionManager
    print("2️⃣  Probando SessionManager...")
    session_mgr = SessionManager()
    session_start = session_mgr.start_session()
    print(f"   Sesión iniciada: {session_start}")
    print(f"   Información: {session_mgr.get_session_info()}\n")

    if session_start:
        session_mgr.record_operation()
        session_mgr.record_operation()
        print(f"3️⃣  Después de 2 operaciones:")
        print(f"   Información: {session_mgr.get_session_info()}\n")
        session_mgr.end_session()

    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
