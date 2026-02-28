"""
Aplicación web Flask para Goleador SMS Marketing
Dashboard y panel de control
"""
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from datetime import datetime, timedelta
from auth import SessionManager
from report_generator import ReportGenerator
from analytics import Analytics
from task_manager import TaskManager
from sms_sender import SMSSender
from cache import BalanceCache
from mock_data import mock_provider

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
app.secret_key = "goleador_sms_marketing_secret_key"
CORS(app)

# Inicializar componentes
session_manager = SessionManager()
report_gen = ReportGenerator()
analytics = Analytics()
task_manager = TaskManager()
sms_sender = SMSSender()
balance_cache = BalanceCache(ttl=300)

logger.info("🚀 Aplicación Flask inicializada")


# ==================== RUTAS PRINCIPALES ====================

@app.route("/")
def index():
    """Página principal"""
    logger.info("📄 GET /")
    # ⚠️ AUTENTICACIÓN DESHABILITADA - Acceso directo al dashboard
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Página de login"""
    logger.info(f"📝 {request.method} /login")
    # ⚠️ AUTENTICACIÓN DESHABILITADA - Acceso directo al dashboard
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    """Cerrar sesión"""
    logger.info("👋 GET /logout")
    session_manager.end_session()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    """Dashboard principal"""
    logger.info("📊 GET /dashboard")
    # ⚠️ AUTENTICACIÓN DESHABILITADA - Acceso directo
    return render_template("dashboard.html")


# ==================== API: DASHBOARD ====================

@app.route("/api/dashboard/stats")
def api_dashboard_stats():
    """Obtener estadísticas del dashboard"""
    logger.info("📊 GET /api/dashboard/stats")

    try:
        kpis = analytics.calculate_kpis()
        summary = report_gen.generate_activity_summary()

        return jsonify({
            "code": 0,
            "data": {
                "kpis": kpis,
                "summary": summary["summary"]
            }
        })
    except Exception as e:
        logger.warning(f"⚠️ Error obteniendo datos reales: {str(e)}")
        logger.info("📦 Usando datos simulados...")
        # Fallback a mock data
        return jsonify({
            "code": 0,
            "data": {
                "kpis": mock_provider.get_kpis(),
                "summary": mock_provider.get_activity_summary()["summary"]
            }
        })


@app.route("/api/dashboard/balance")
def api_dashboard_balance():
    """Obtener balance de la cuenta"""
    logger.info("📊 GET /api/dashboard/balance")

    try:
        # Verificar caché
        cached = balance_cache.get_balance()
        if cached:
            logger.info("✅ Balance desde caché")
            return jsonify({"code": 0, "data": cached})

        # Obtener de la API
        result = sms_sender.api.get_balance()

        if result.get("code") == 0:
            balance_cache.set_balance(result)
            return jsonify({"code": 0, "data": result})
        else:
            logger.warning(f"⚠️ API retornó error: {result.get('code')}")
            logger.info("📦 Usando balance simulado...")
            # Fallback a mock data
            return jsonify({"code": 0, "data": mock_provider.get_balance()})

    except Exception as e:
        logger.warning(f"⚠️ Error obteniendo balance: {str(e)}")
        logger.info("📦 Usando balance simulado...")
        # Fallback a mock data
        return jsonify({"code": 0, "data": mock_provider.get_balance()})


@app.route("/api/dashboard/hourly")
def api_dashboard_hourly():
    """Obtener distribución por hora"""
    logger.info("📊 GET /api/dashboard/hourly")

    try:
        hourly = analytics.get_hourly_distribution()
        return jsonify({"code": 0, "data": hourly})
    except Exception as e:
        logger.warning(f"⚠️ Error obteniendo distribución: {str(e)}")
        logger.info("📦 Usando distribución simulada...")
        return jsonify({"code": 0, "data": mock_provider.get_hourly_distribution()})


@app.route("/api/dashboard/insights")
def api_dashboard_insights():
    """Obtener insights automáticos"""
    logger.info("💡 GET /api/dashboard/insights")

    try:
        insights = analytics.generate_insights()
        return jsonify({"code": 0, "insights": insights})
    except Exception as e:
        logger.warning(f"⚠️ Error obteniendo insights: {str(e)}")
        logger.info("📦 Usando insights simulados...")
        return jsonify({"code": 0, "insights": mock_provider.get_insights()["insights"]})


# ==================== API: SMS ====================

@app.route("/api/sms/send", methods=["POST"])
def api_sms_send():
    """Enviar SMS"""
    logger.info("📤 POST /api/sms/send")

    try:
        data = request.get_json()

        result = sms_sender.send_sms(
            numbers=data.get("numbers", []),
            content=data.get("content", ""),
            sender=data.get("sender")
        )

        return jsonify(result)
    except Exception as e:
        logger.warning(f"⚠️ Error enviando SMS: {str(e)}")
        logger.info("📦 Simulando envío de SMS...")
        # Fallback a mock data
        data = request.get_json()
        return jsonify(mock_provider.send_sms_mock(
            numbers=data.get("numbers", []),
            content=data.get("content", "")
        ))


@app.route("/api/sms/history")
def api_sms_history():
    """Obtener histórico de SMS"""
    logger.info("📋 GET /api/sms/history")

    try:
        limit = request.args.get("limit", 100, type=int)
        sms_list = report_gen.db.get_all_sms(limit=limit)

        return jsonify({"code": 0, "data": sms_list})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


# ==================== API: REPORTES ====================

@app.route("/api/reports/sms")
def api_reports_sms():
    """Obtener reporte de SMS"""
    logger.info("📊 GET /api/reports/sms")

    try:
        report = report_gen.generate_sms_report()
        return jsonify({"code": 0, "data": report})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/reports/delivery")
def api_reports_delivery():
    """Obtener reporte de entrega"""
    logger.info("📋 GET /api/reports/delivery")

    try:
        report = report_gen.generate_delivery_report()
        return jsonify({"code": 0, "data": report})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/reports/transactions")
def api_reports_transactions():
    """Obtener reporte de transacciones"""
    logger.info("💰 GET /api/reports/transactions")

    try:
        report = report_gen.generate_transaction_report()
        return jsonify({"code": 0, "data": report})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


# ==================== API: TAREAS ====================

@app.route("/api/tasks/create", methods=["POST"])
def api_tasks_create():
    """Crear nueva tarea"""
    logger.info("➕ POST /api/tasks/create")

    try:
        data = request.get_json()

        task_id = task_manager.create_task(
            task_type=data.get("task_type", 0),
            contacts=data.get("contacts", []),
            content=data.get("content", ""),
            sender=data.get("sender"),
            sendtime=data.get("sendtime"),
            interval=data.get("interval"),
            endtime=data.get("endtime")
        )

        return jsonify({"code": 0, "task_id": task_id})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/tasks/list")
def api_tasks_list():
    """Listar tareas"""
    logger.info("📋 GET /api/tasks/list")

    try:
        status = request.args.get("status")
        tasks = task_manager.list_tasks(status=status)

        return jsonify({"code": 0, "data": tasks})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/tasks/<task_id>/pause", methods=["POST"])
def api_tasks_pause(task_id):
    """Pausar tarea"""
    logger.info(f"⏸️  POST /api/tasks/{task_id}/pause")

    try:
        task_manager.pause_task(task_id)
        return jsonify({"code": 0, "message": "Tarea pausada"})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/tasks/<task_id>/resume", methods=["POST"])
def api_tasks_resume(task_id):
    """Reanudar tarea"""
    logger.info(f"▶️  POST /api/tasks/{task_id}/resume")

    try:
        task_manager.resume_task(task_id)
        return jsonify({"code": 0, "message": "Tarea reanudada"})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/tasks/<task_id>/cancel", methods=["POST"])
def api_tasks_cancel(task_id):
    """Cancelar tarea"""
    logger.info(f"❌ POST /api/tasks/{task_id}/cancel")

    try:
        task_manager.cancel_task(task_id)
        return jsonify({"code": 0, "message": "Tarea cancelada"})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


# ==================== API: CAMPAÑAS DINÁMICAS ====================

@app.route("/api/campaigns/upload", methods=["POST"])
def api_campaigns_upload():
    """Cargar archivo Excel con contactos"""
    logger.info("📤 POST /api/campaigns/upload")

    try:
        # Verificar que se envió archivo
        if 'file' not in request.files:
            return jsonify({"code": -1, "error": "No se envió archivo"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"code": -1, "error": "Archivo vacío"}), 400

        # Importar excel_loader
        from excel_loader import excel_loader

        # Guardar temporalmente
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp.name)
            result = excel_loader.read_excel(tmp.name)

        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/campaigns/create", methods=["POST"])
def api_campaigns_create():
    """Crear campaña con Excel cargado"""
    logger.info("📝 POST /api/campaigns/create")

    try:
        data = request.get_json()

        import uuid
        from campaign_processor import campaign_processor

        campaign_id = str(uuid.uuid4())

        result = campaign_processor.create_campaign(
            campaign_id=campaign_id,
            name=data.get('name', 'Sin nombre'),
            excel_import_id=data.get('excel_import_id'),
            template=data.get('template', '')
        )

        if result['success']:
            return jsonify({
                "code": 0,
                "campaign_id": campaign_id,
                "message": "Campaña creada"
            })
        else:
            return jsonify({
                "code": -1,
                "error": result['error']
            }), 400

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/campaigns/<campaign_id>/process", methods=["POST"])
def api_campaigns_process(campaign_id):
    """Procesar campaña y sustituir variables"""
    logger.info(f"⚙️ POST /api/campaigns/{campaign_id}/process")

    try:
        data = request.get_json()
        from campaign_processor import campaign_processor

        result = campaign_processor.process_contacts(
            campaign_id=campaign_id,
            contacts=data.get('contacts', []),
            template=data.get('template', '')
        )

        return jsonify({
            "code": 0 if result['success'] else -1,
            "data": result
        })

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/campaigns/<campaign_id>/send", methods=["POST"])
def api_campaigns_send(campaign_id):
    """Enviar campaña masiva"""
    logger.info(f"🚀 POST /api/campaigns/{campaign_id}/send")

    try:
        from campaign_processor import campaign_processor

        result = campaign_processor.send_campaign(campaign_id)

        return jsonify({
            "code": 0 if result['success'] else -1,
            "data": result
        })

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


@app.route("/api/campaigns/<campaign_id>/progress", methods=["GET"])
def api_campaigns_progress(campaign_id):
    """Obtener progreso de campaña"""
    logger.info(f"📊 GET /api/campaigns/{campaign_id}/progress")

    try:
        from campaign_processor import campaign_processor

        progress = campaign_processor.get_progress(campaign_id)

        return jsonify({
            "code": 0,
            "data": progress
        })

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({"code": -1, "error": str(e)}), 500


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found(error):
    """Página no encontrada"""
    logger.warning(f"404: {request.path}")
    return jsonify({"code": 404, "error": "Página no encontrada"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Error interno del servidor"""
    logger.error(f"500: {str(error)}")
    return jsonify({"code": 500, "error": "Error interno del servidor"}), 500


# ==================== INICIALIZACIÓN ====================

if __name__ == "__main__":
    logger.info("🚀 Iniciando servidor Flask...")
    logger.info("📍 Acceda a http://localhost:5000")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )
