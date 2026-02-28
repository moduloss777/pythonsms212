"""
Procesador avanzado de mensajes
Valida, sanitiza, optimiza y transforma contenido de SMS
"""
import logging
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Procesador completo de mensajes"""

    # Mapeo de caracteres problemáticos
    CHAR_MAP = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
        "â": "a", "ê": "e", "î": "i", "ô": "o", "û": "u",
        "ã": "a", "õ": "o", "ñ": "n",
        "ç": "c",
        "«": '"', "»": '"',
    }

    # Caracteres permitidos
    ALLOWED_CHARS_PATTERN = re.compile(r"[^a-zA-Z0-9\s\.\,\!\?\-\(\)\'\"\&\$\€\@\#\%\+\=\*\/\\\_\:\;\~\<\>\[\]\{\}]")

    def __init__(self):
        """Inicializar procesador"""
        self.processing_log = []

    def normalize_text(self, text: str, preserve_accents: bool = False) -> str:
        """
        Normalizar texto

        Args:
            text: Texto a normalizar
            preserve_accents: Mantener acentos

        Returns:
            Texto normalizado
        """
        if preserve_accents:
            return text

        normalized = text
        for accent_char, replacement in self.CHAR_MAP.items():
            normalized = normalized.replace(accent_char, replacement)

        return normalized

    def remove_special_chars(self, text: str) -> str:
        """
        Remover caracteres especiales problemáticos

        Args:
            text: Texto a limpiar

        Returns:
            Texto limpio
        """
        # Remover caracteres no permitidos
        cleaned = self.ALLOWED_CHARS_PATTERN.sub("", text)
        # Remover espacios múltiples
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def shorten_url(self, text: str, replace_with: str = "URL") -> str:
        """
        Acortar URLs en el texto

        Args:
            text: Texto con URLs
            replace_with: Reemplazo para URLs

        Returns:
            Texto con URLs acortadas
        """
        url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$\-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        return re.sub(url_pattern, replace_with, text)

    def replace_emojis(self, text: str, preserve_emojis: bool = False) -> str:
        """
        Reemplazar emojis

        Args:
            text: Texto con posibles emojis
            preserve_emojis: Si False, remover emojis

        Returns:
            Texto procesado
        """
        if preserve_emojis:
            return text

        # Remover emojis (rango Unicode)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Símbolos
            "\U0001F680-\U0001F6FF"  # Transporte
            "\U0001F1E0-\U0001F1FF"  # Banderas
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r"", text)

    def add_prefix(self, text: str, prefix: str) -> str:
        """
        Agregar prefijo al mensaje

        Args:
            text: Texto original
            prefix: Prefijo a agregar

        Returns:
            Texto con prefijo
        """
        return f"{prefix} {text}"

    def add_suffix(self, text: str, suffix: str) -> str:
        """
        Agregar sufijo al mensaje

        Args:
            text: Texto original
            suffix: Sufijo a agregar

        Returns:
            Texto con sufijo
        """
        return f"{text} {suffix}"

    def replace_variables(self, text: str, variables: Dict[str, str]) -> str:
        """
        Reemplazar variables en el texto

        Args:
            text: Texto con variables {{var}}
            variables: Dict de variables

        Returns:
            Texto procesado
        """
        result = text
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, var_value)

        return result

    def add_unsubscribe_link(self, text: str, code: str) -> str:
        """
        Agregar enlace de desuscripción

        Args:
            text: Texto original
            code: Código de desuscripción

        Returns:
            Texto con enlace
        """
        unsubscribe_text = f"Desuscribirse: {code}"
        return f"{text}\n{unsubscribe_text}"

    def validate_length(self, text: str, max_length: int = 1024) -> Tuple[bool, int]:
        """
        Validar longitud del mensaje

        Args:
            text: Texto a validar
            max_length: Longitud máxima

        Returns:
            Tupla (es_válido, longitud)
        """
        length = len(text)
        is_valid = length <= max_length

        if not is_valid:
            logger.warning(f"⚠️  Mensaje demasiado largo: {length}/{max_length}")

        return is_valid, length

    def process(self, text: str, options: Optional[Dict] = None) -> Dict:
        """
        Procesar mensaje completo

        Args:
            text: Texto a procesar
            options: Dict con opciones de procesamiento:
                - normalize_accents: normalizar acentos
                - remove_special_chars: remover especiales
                - shorten_urls: acortar URLs
                - remove_emojis: remover emojis
                - prefix: agregar prefijo
                - suffix: agregar sufijo
                - variables: reemplazar variables
                - unsubscribe_code: agregar desuscripción

        Returns:
            Dict con texto procesado y metadata
        """
        options = options or {}
        original_text = text
        processed_text = text

        logger.info(f"📝 Procesando mensaje ({len(text)} caracteres)...")

        # Normalizar acentos
        if options.get("normalize_accents", True):
            processed_text = self.normalize_text(processed_text, preserve_accents=False)

        # Remover caracteres especiales
        if options.get("remove_special_chars", False):
            processed_text = self.remove_special_chars(processed_text)

        # Acortar URLs
        if options.get("shorten_urls", False):
            processed_text = self.shorten_url(processed_text)

        # Remover emojis
        if options.get("remove_emojis", True):
            processed_text = self.replace_emojis(processed_text, preserve_emojis=False)

        # Agregar prefijo
        if "prefix" in options and options["prefix"]:
            processed_text = self.add_prefix(processed_text, options["prefix"])

        # Agregar sufijo
        if "suffix" in options and options["suffix"]:
            processed_text = self.add_suffix(processed_text, options["suffix"])

        # Reemplazar variables
        if "variables" in options:
            processed_text = self.replace_variables(processed_text, options["variables"])

        # Agregar desuscripción
        if "unsubscribe_code" in options:
            processed_text = self.add_unsubscribe_link(processed_text, options["unsubscribe_code"])

        # Validar longitud
        is_valid, length = self.validate_length(processed_text)

        result = {
            "original": original_text,
            "processed": processed_text,
            "length": length,
            "is_valid": is_valid,
            "changes_made": original_text != processed_text,
            "processed_at": datetime.now().isoformat()
        }

        self.processing_log.append(result)
        logger.info(f"✅ Mensaje procesado ({length} caracteres, válido: {is_valid})")

        return result

    def batch_process(self, messages: List[str], options: Optional[Dict] = None) -> List[Dict]:
        """
        Procesar múltiples mensajes

        Args:
            messages: Lista de mensajes
            options: Opciones de procesamiento

        Returns:
            Lista de resultados
        """
        logger.info(f"📦 Procesando {len(messages)} mensajes...")

        results = []
        for i, message in enumerate(messages, 1):
            result = self.process(message, options)
            results.append(result)
            logger.debug(f"  {i}/{len(messages)} ✅")

        return results

    def get_processing_log(self) -> List[Dict]:
        """Obtener log de procesamiento"""
        return self.processing_log

    def clear_log(self):
        """Limpiar log"""
        self.processing_log.clear()


class MessageTemplate:
    """Gestor de plantillas de mensajes"""

    def __init__(self):
        """Inicializar gestor de plantillas"""
        self.templates = {}
        self.processor = MessageProcessor()

    def register_template(self, name: str, template: str):
        """
        Registrar plantilla

        Args:
            name: Nombre de la plantilla
            template: Contenido de la plantilla
        """
        self.templates[name] = template
        logger.info(f"📝 Plantilla registrada: {name}")

    def render(self, template_name: str, variables: Dict[str, str]) -> Dict:
        """
        Renderizar plantilla

        Args:
            template_name: Nombre de la plantilla
            variables: Variables a reemplazar

        Returns:
            Resultado con mensaje renderizado
        """
        if template_name not in self.templates:
            return {
                "code": -1,
                "error": f"Plantilla no encontrada: {template_name}"
            }

        template = self.templates[template_name]
        message = self.processor.replace_variables(template, variables)

        return {
            "code": 0,
            "template": template_name,
            "message": message,
            "variables_used": variables
        }

    def list_templates(self) -> List[str]:
        """Listar plantillas registradas"""
        return list(self.templates.keys())


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL PROCESADOR DE MENSAJES")
    print("="*60 + "\n")

    processor = MessageProcessor()

    # Test 1: Procesamiento básico
    print("1️⃣  Procesamiento básico...")
    result = processor.process(
        "Hola mundo 🌍",
        options={"remove_emojis": True}
    )
    print(f"   Original: {result['original']}")
    print(f"   Procesado: {result['processed']}\n")

    # Test 2: Con plantilla
    print("2️⃣  Plantillas...")
    template = MessageTemplate()
    template.register_template(
        "promo",
        "Hola {{name}}, ¡tienes {{discount}}% de descuento!"
    )
    result = template.render("promo", {"name": "Juan", "discount": "50"})
    print(f"   Mensaje: {result['message']}\n")

    # Test 3: Batch processing
    print("3️⃣  Procesamiento en lotes...")
    messages = ["Mensaje 1 🚀", "Mensaje 2 ✅", "Mensaje 3 ❌"]
    results = processor.batch_process(messages, {"remove_emojis": True})
    print(f"   Procesados: {len(results)}\n")

    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
