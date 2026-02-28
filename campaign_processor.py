"""
CAMPAIGN PROCESSOR - Procesamiento y envío de campañas masivas
Goleador SMS Marketing - Manejo de Campañas Dinámicas
"""

import logging
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from database import Database
from sms_sender import SMSSender
from message_processor import MessageProcessor

logger = logging.getLogger(__name__)

@dataclass
class CampaignStatus:
    """Estado de una campaña"""
    campaign_id: str
    status: str  # draft, ready, sending, completed, failed
    sent: int = 0
    failed: int = 0
    total: int = 0
    errors: List[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CampaignProcessor:
    """
    Procesador de campañas SMS con sustitución de variables dinámicas
    """

    def __init__(self):
        """Inicializar procesador"""
        self.db = Database()
        self.sms_sender = SMSSender()
        self.message_processor = MessageProcessor()
        self.campaign_status = {}  # Diccionario de estados en tiempo real
        logger.info("✅ CampaignProcessor inicializado")

    def create_campaign(self, campaign_id: str, name: str, excel_import_id: str, template: str) -> Dict:
        """
        Crear nueva campaña

        Args:
            campaign_id: ID único de la campaña
            name: Nombre de la campaña
            excel_import_id: ID de importación de Excel
            template: Plantilla de mensaje con variables

        Returns:
            Dict con resultado
        """
        logger.info(f"📝 Creando campaña: {name}")

        try:
            # Verificar que la importación existe
            if not self._verify_excel_import(excel_import_id):
                return {
                    "success": False,
                    "error": "Excel import no encontrado",
                    "campaign_id": None
                }

            # Insertar en BD
            query = """
            INSERT INTO dynamic_campaigns (id, name, excel_import_id, template, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.execute_query(
                query,
                (campaign_id, name, excel_import_id, template, datetime.now().isoformat(), 'draft')
            )
            self.db.commit()

            # Inicializar estado
            self.campaign_status[campaign_id] = CampaignStatus(
                campaign_id=campaign_id,
                status='draft',
                total=0
            )

            logger.info(f"✅ Campaña creada: {campaign_id}")

            return {
                "success": True,
                "campaign_id": campaign_id,
                "message": f"Campaña '{name}' creada"
            }

        except Exception as e:
            logger.error(f"❌ Error creando campaña: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "campaign_id": None
            }

    def process_contacts(self, campaign_id: str, contacts: List[Dict], template: str) -> Dict:
        """
        Procesar contactos y sustituir variables en plantilla

        Args:
            campaign_id: ID de la campaña
            contacts: Lista de contactos con variables
            template: Plantilla con {{variables}}

        Returns:
            Dict con contactos procesados
        """
        logger.info(f"⚙️ Procesando {len(contacts)} contactos para campaña {campaign_id}")

        try:
            processed_contacts = []
            errors = []

            for idx, contact in enumerate(contacts):
                try:
                    # Sustituir variables en la plantilla
                    processed_message = template
                    variables = contact.get('variables', {})

                    for var_name, var_value in variables.items():
                        placeholder = f"{{{{{var_name}}}}}"
                        processed_message = processed_message.replace(placeholder, str(var_value))

                    # Verificar longitud del mensaje
                    if len(processed_message) > 1000:
                        errors.append(f"Contacto {idx + 1}: Mensaje muy largo ({len(processed_message)} chars)")
                        continue

                    processed_contact = {
                        "id": str(uuid.uuid4()),
                        "campaign_id": campaign_id,
                        "numero": contact['numero'],
                        "nombre": contact.get('nombre', ''),
                        "variables": variables,
                        "processed_message": processed_message,
                        "status": "pending",
                        "created_at": datetime.now().isoformat()
                    }

                    processed_contacts.append(processed_contact)

                except Exception as e:
                    errors.append(f"Contacto {idx + 1}: Error: {str(e)}")

            # Guardar en BD
            if processed_contacts:
                self._save_campaign_contacts(processed_contacts)

            self.campaign_status[campaign_id].total = len(processed_contacts)

            logger.info(f"✅ {len(processed_contacts)} contactos procesados")

            return {
                "success": True,
                "total_contacts": len(processed_contacts),
                "errors": errors,
                "sample_message": processed_contacts[0]['processed_message'] if processed_contacts else "",
                "contacts": processed_contacts
            }

        except Exception as e:
            logger.error(f"❌ Error procesando contactos: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_contacts": 0,
                "errors": [str(e)]
            }

    def send_campaign(self, campaign_id: str) -> Dict:
        """
        Enviar campaña masiva (inicia en thread separado)

        Args:
            campaign_id: ID de la campaña

        Returns:
            Dict con resultado
        """
        logger.info(f"🚀 Iniciando envío de campaña: {campaign_id}")

        try:
            # Verificar campaña existe
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return {
                    "success": False,
                    "error": "Campaña no encontrada"
                }

            # Obtener contactos
            contacts = self._get_campaign_contacts(campaign_id)
            if not contacts:
                return {
                    "success": False,
                    "error": "No hay contactos para enviar"
                }

            # Iniciar envío en thread separado
            status = self.campaign_status[campaign_id]
            status.status = 'sending'
            status.started_at = datetime.now().isoformat()

            thread = threading.Thread(
                target=self._send_campaign_worker,
                args=(campaign_id, contacts, campaign['template']),
                daemon=True
            )
            thread.start()

            return {
                "success": True,
                "campaign_id": campaign_id,
                "message": f"Iniciando envío de {len(contacts)} SMS",
                "job_id": str(uuid.uuid4())
            }

        except Exception as e:
            logger.error(f"❌ Error iniciando envío: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _send_campaign_worker(self, campaign_id: str, contacts: List[Dict], template: str):
        """
        Worker thread para enviar campaña (ejecución en background)
        """
        logger.info(f"👷 Worker iniciado para campaña {campaign_id}")

        status = self.campaign_status[campaign_id]
        results = {"sent": 0, "failed": 0}

        try:
            for idx, contact in enumerate(contacts):
                try:
                    # Obtener mensaje procesado
                    message = contact.get('processed_message', template)

                    # Enviar SMS
                    response = self.sms_sender.send_sms(
                        numbers=[contact['numero']],
                        content=message,
                        sender=None
                    )

                    if response.get('code') == 0:
                        # Actualizar estado en BD
                        self._update_contact_status(
                            contact['id'],
                            'sent',
                            datetime.now().isoformat()
                        )
                        results['sent'] += 1
                        status.sent += 1
                    else:
                        self._update_contact_status(
                            contact['id'],
                            'failed',
                            error=response.get('error', 'Unknown error')
                        )
                        results['failed'] += 1
                        status.failed += 1

                except Exception as e:
                    logger.error(f"❌ Error enviando a {contact['numero']}: {str(e)}")
                    self._update_contact_status(
                        contact['id'],
                        'failed',
                        error=str(e)
                    )
                    results['failed'] += 1
                    status.failed += 1

                # Pequeña pausa para no saturar API
                time.sleep(0.1)

            # Marcar como completada
            status.status = 'completed'
            status.completed_at = datetime.now().isoformat()
            self._update_campaign_status(campaign_id, 'completed')

            logger.info(f"✅ Campaña {campaign_id} completada: {results['sent']} enviados, {results['failed']} fallidos")

        except Exception as e:
            logger.error(f"❌ Error en worker: {str(e)}")
            status.status = 'failed'
            status.errors.append(str(e))
            self._update_campaign_status(campaign_id, 'failed')

    def get_progress(self, campaign_id: str) -> Dict:
        """
        Obtener progreso de una campaña

        Args:
            campaign_id: ID de la campaña

        Returns:
            Dict con estado actual
        """
        if campaign_id not in self.campaign_status:
            return {
                "status": "unknown",
                "sent": 0,
                "failed": 0,
                "total": 0,
                "percentage": 0
            }

        status = self.campaign_status[campaign_id]
        total = status.total or 1  # Evitar división por cero
        percentage = int((status.sent + status.failed) / total * 100)

        return {
            "campaign_id": campaign_id,
            "status": status.status,
            "sent": status.sent,
            "failed": status.failed,
            "total": status.total,
            "percentage": percentage,
            "started_at": status.started_at,
            "completed_at": status.completed_at,
            "errors": status.errors
        }

    # ============= MÉTODOS PRIVADOS =============

    def _verify_excel_import(self, excel_import_id: str) -> bool:
        """Verificar que una importación de Excel existe"""
        # Por ahora, siempre retornar True (implementar BD después)
        return True

    def _get_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Obtener campaña de BD"""
        # Por ahora, retornar campaign template
        return {
            "id": campaign_id,
            "template": "Hola {{nombre}}, tienes {{descuento}}% de descuento"
        }

    def _get_campaign_contacts(self, campaign_id: str) -> List[Dict]:
        """Obtener contactos de una campaña"""
        # Por ahora, retornar lista vacía (implementar BD después)
        return []

    def _save_campaign_contacts(self, contacts: List[Dict]):
        """Guardar contactos en BD"""
        logger.info(f"💾 Guardando {len(contacts)} contactos en BD")
        # Implementar guardado en BD

    def _update_contact_status(self, contact_id: str, status: str, sent_at: Optional[str] = None, error: Optional[str] = None):
        """Actualizar estado de un contacto"""
        logger.info(f"📝 Actualizando contacto {contact_id}: {status}")
        # Implementar actualización en BD

    def _update_campaign_status(self, campaign_id: str, status: str):
        """Actualizar estado de campaña en BD"""
        logger.info(f"📝 Actualizando campaña {campaign_id}: {status}")
        # Implementar actualización en BD


# Instancia global
campaign_processor = CampaignProcessor()
