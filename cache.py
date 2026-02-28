"""
Sistema de caché para resultados de API
Mejora rendimiento evitando llamadas repetidas
"""
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from hashlib import md5
import json

logger = logging.getLogger(__name__)


class CacheEntry:
    """Entrada individual de caché"""

    def __init__(self, key: str, value: Any, ttl: int = 300):
        """
        Crear entrada de caché

        Args:
            key: Clave única
            value: Valor a cachear
            ttl: Tiempo de vida en segundos
        """
        self.key = key
        self.value = value
        self.created_at = datetime.now()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = datetime.now()

    def is_expired(self) -> bool:
        """Verificar si la entrada ha expirado"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl

    def access(self) -> Any:
        """Acceder al valor y actualizar estadísticas"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value

    def get_age(self) -> float:
        """Obtener edad en segundos"""
        return (datetime.now() - self.created_at).total_seconds()

    def __str__(self):
        return (
            f"CacheEntry(key={self.key}, age={self.get_age():.1f}s, "
            f"ttl={self.ttl}s, accesses={self.access_count})"
        )


class Cache:
    """Sistema de caché en memoria"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Inicializar caché

        Args:
            max_size: Máximo número de entradas
            default_ttl: TTL por defecto en segundos
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def _generate_key(self, *args, **kwargs) -> str:
        """
        Generar clave única para parámetros

        Args:
            *args: Argumentos
            **kwargs: Argumentos clave-valor

        Returns:
            Hash único
        """
        key_str = json.dumps(
            (args, kwargs),
            sort_keys=True,
            default=str
        )
        return md5(key_str.encode()).hexdigest()

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Guardar valor en caché

        Args:
            key: Clave única
            value: Valor a cachear
            ttl: Tiempo de vida (usa default si es None)
        """
        ttl = ttl or self.default_ttl

        # Limpiar entradas expiradas si estamos cerca del límite
        if len(self.cache) >= self.max_size:
            self._cleanup()

        self.cache[key] = CacheEntry(key, value, ttl)
        logger.debug(f"💾 Caché set: {key} (TTL: {ttl}s)")

    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del caché

        Args:
            key: Clave a buscar

        Returns:
            Valor si existe y no expiró, None en caso contrario
        """
        if key not in self.cache:
            self.misses += 1
            logger.debug(f"❌ Caché miss: {key}")
            return None

        entry = self.cache[key]

        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            logger.debug(f"⏰ Caché expirado: {key}")
            return None

        self.hits += 1
        value = entry.access()
        logger.debug(f"✅ Caché hit: {key}")
        return value

    def exists(self, key: str) -> bool:
        """
        Verificar si una clave existe y no está expirada

        Args:
            key: Clave a verificar

        Returns:
            True si existe y es válida
        """
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """
        Eliminar entrada del caché

        Args:
            key: Clave a eliminar

        Returns:
            True si fue eliminada, False si no existía
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"🗑️  Caché borrado: {key}")
            return True
        return False

    def clear(self):
        """Limpiar todo el caché"""
        size = len(self.cache)
        self.cache.clear()
        logger.info(f"🧹 Caché limpiado ({size} entradas)")

    def _cleanup(self):
        """Limpiar entradas expiradas"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self.cache[key]

        logger.debug(f"🧹 Limpieza de caché: {len(expired_keys)} entradas expiradas")

    def get_stats(self) -> Dict:
        """
        Obtener estadísticas de caché

        Returns:
            Dict con estadísticas
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "total_requests": total_requests
        }

    def get_entries_info(self) -> list:
        """
        Obtener información de todas las entradas

        Returns:
            Lista de información de entradas
        """
        return [
            {
                "key": key,
                "age": entry.get_age(),
                "ttl": entry.ttl,
                "accesses": entry.access_count,
                "expired": entry.is_expired()
            }
            for key, entry in self.cache.items()
        ]

    def __str__(self):
        stats = self.get_stats()
        return (
            f"Cache(size={stats['size']}/{stats['max_size']}, "
            f"hits={stats['hits']}, misses={stats['misses']}, "
            f"hit_rate={stats['hit_rate']})"
        )


class BalanceCache:
    """Caché especializado para balance de cuenta"""

    def __init__(self, ttl: int = 60):
        """
        Inicializar caché de balance

        Args:
            ttl: Tiempo de vida del balance en segundos
        """
        self.cache = Cache(max_size=10, default_ttl=ttl)
        self.balance_key = "account_balance"

    def get_balance(self) -> Optional[Dict]:
        """Obtener balance del caché"""
        return self.cache.get(self.balance_key)

    def set_balance(self, balance: Dict, ttl: Optional[int] = None):
        """Guardar balance en caché"""
        self.cache.set(self.balance_key, balance, ttl)

    def is_cached(self) -> bool:
        """Verificar si balance está en caché"""
        return self.cache.exists(self.balance_key)

    def clear(self):
        """Limpiar caché de balance"""
        self.cache.clear()

    def get_stats(self) -> Dict:
        """Obtener estadísticas"""
        return self.cache.get_stats()


class ReportCache:
    """Caché especializado para reportes de SMS"""

    def __init__(self, ttl: int = 300):
        """
        Inicializar caché de reportes

        Args:
            ttl: Tiempo de vida en segundos
        """
        self.cache = Cache(max_size=500, default_ttl=ttl)

    def get_report(self, sms_id: str) -> Optional[Dict]:
        """Obtener reporte del caché"""
        return self.cache.get(f"report_{sms_id}")

    def set_report(self, sms_id: str, report: Dict, ttl: Optional[int] = None):
        """Guardar reporte en caché"""
        self.cache.set(f"report_{sms_id}", report, ttl)

    def clear_report(self, sms_id: str) -> bool:
        """Limpiar reporte específico"""
        return self.cache.delete(f"report_{sms_id}")

    def clear_all(self):
        """Limpiar todos los reportes"""
        self.cache.clear()

    def get_stats(self) -> Dict:
        """Obtener estadísticas"""
        return self.cache.get_stats()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL SISTEMA DE CACHÉ")
    print("="*60 + "\n")

    # Test 1: Cache básico
    print("1️⃣  Probando Cache básico...")
    cache = Cache(max_size=100, default_ttl=5)

    cache.set("user:1", {"name": "Juan", "age": 30})
    cache.set("user:2", {"name": "María", "age": 25})

    print(f"   user:1 = {cache.get('user:1')}")
    print(f"   user:2 = {cache.get('user:2')}")
    print(f"   user:3 = {cache.get('user:3')}")  # No existe
    print(f"   Stats: {cache.get_stats()}\n")

    # Test 2: BalanceCache
    print("2️⃣  Probando BalanceCache...")
    balance_cache = BalanceCache(ttl=10)

    balance = {"code": 0, "balance": 1000, "gift_balance": 50}
    balance_cache.set_balance(balance)

    cached_balance = balance_cache.get_balance()
    print(f"   Balance cacheado: {cached_balance}")
    print(f"   ¿Está en caché?: {balance_cache.is_cached()}")
    print(f"   Stats: {balance_cache.get_stats()}\n")

    # Test 3: ReportCache
    print("3️⃣  Probando ReportCache...")
    report_cache = ReportCache(ttl=300)

    report1 = {"code": 0, "status": "delivered"}
    report2 = {"code": 0, "status": "failed"}

    report_cache.set_report("SMS001", report1)
    report_cache.set_report("SMS002", report2)

    print(f"   SMS001: {report_cache.get_report('SMS001')}")
    print(f"   SMS002: {report_cache.get_report('SMS002')}")
    print(f"   Stats: {report_cache.get_stats()}\n")

    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
