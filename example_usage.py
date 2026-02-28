"""
Ejemplo de uso completo de Traffilink API
Demuestra cómo usar la API en casos reales
"""
import json
from traffilink_api import TrafficLinkAPI
from utils import PhoneValidator, MessageValidator, SMSStatistics
from models import DataStorage, Account, SMS, SMSStatus


def print_separator(title: str = ""):
    """Imprimir separador con título"""
    if title:
        print(f"\n{'='*60}\n{title}\n{'='*60}")
    else:
        print(f"\n{'='*60}")


def example_1_get_balance():
    """Ejemplo 1: Obtener balance de cuenta"""
    print_separator("📊 EJEMPLO 1: OBTENER BALANCE")

    api = TrafficLinkAPI()

    print("\n🔍 Consultando balance...")
    response = api.get_balance()

    print(f"\nRespuesta completa:")
    print(json.dumps(response, indent=2, ensure_ascii=False))

    if response.get('code') == 0:
        print(f"\n✅ Balance actual:")
        print(f"   💰 Saldo: ${response.get('balance', 0)}")
        print(f"   🎁 Saldo regalo: ${response.get('gift_balance', 0)}")
        print(f"   📊 Total: ${response.get('balance', 0) + response.get('gift_balance', 0)}")
    else:
        print(f"\n❌ Error: {response.get('error_message')}")


def example_2_send_single_sms():
    """Ejemplo 2: Enviar un SMS simple"""
    print_separator("📱 EJEMPLO 2: ENVIAR SMS ÚNICO")

    api = TrafficLinkAPI()
    stats = SMSStatistics()

    # Número y contenido
    numero = "3001234567"  # Reemplazar con número real
    mensaje = "¡Hola! Este es mi primer SMS con Traffilink API 🚀"

    # Validar
    print(f"\n✓ Número: {numero}")
    es_valido = PhoneValidator.validate_number(numero)
    print(f"  Válido: {'✅' if es_valido else '❌'}")

    print(f"\n✓ Mensaje: {mensaje}")
    valido, error = MessageValidator.validate_content(mensaje)
    print(f"  Válido: {'✅' if valido else f'❌ {error}'}")
    print(f"  Largo: {len(mensaje)} caracteres")

    if es_valido and valido:
        print(f"\n📤 Enviando SMS...")
        result = api.send_sms(
            numbers=numero,
            content=mensaje,
            sender="GoleadorSMS"  # Remitente opcional
        )

        print(f"\nRespuesta:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get('code') == 0:
            print(f"\n✅ SMS enviado exitosamente")
            print(f"   ID del SMS: {result.get('id')}")
            stats.add_sent(1)
        else:
            print(f"\n❌ Error al enviar: {result.get('error_message')}")
            stats.add_failed(1)

    stats.print_summary()


def example_3_send_multiple_sms():
    """Ejemplo 3: Enviar a múltiples números"""
    print_separator("📱 EJEMPLO 3: ENVIAR A MÚLTIPLES NÚMEROS")

    api = TrafficLinkAPI()
    stats = SMSStatistics()

    # Lista de números
    numeros = [
        "3001234567",
        "3007654321",
        "3009876543"
    ]

    mensaje = "¡Promoción especial! 50% de descuento solo para ti 🎉"

    print(f"\n📋 Números a enviar: {len(numeros)}")
    for num in numeros:
        print(f"   • {num}")

    # Validar números
    validos, invalidos = PhoneValidator.validate_phone_list(numeros)
    print(f"\n✓ Números válidos: {len(validos)}")
    print(f"✗ Números inválidos: {len(invalidos)}")

    if validos:
        print(f"\n📤 Enviando SMS a {len(validos)} números...")
        result = api.send_sms(
            numbers=validos,
            content=mensaje,
            sender="Promo"
        )

        print(f"\nRespuesta:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get('code') == 0:
            print(f"\n✅ SMS enviados exitosamente")
            print(f"   ID: {result.get('id')}")
            stats.add_sent(len(validos))
        else:
            print(f"\n❌ Error: {result.get('error_message')}")

    stats.print_summary()


def example_4_send_batch():
    """Ejemplo 4: Enviar SMS en lotes grandes"""
    print_separator("📦 EJEMPLO 4: ENVIAR EN LOTES (GRAN VOLUMEN)")

    api = TrafficLinkAPI()
    stats = SMSStatistics()

    # Generar lista de números simulados
    print("\n🔄 Generando 25,000 números de prueba...")
    numeros_grandes = [f"300{i:07d}" for i in range(25000)]
    print(f"✓ Números generados: {len(numeros_grandes)}")

    mensaje = "Mensaje para campaña masiva - Lote automático 📢"

    print(f"\n📤 Dividiendo en lotes de 10,000...")
    resultados = api.send_sms_batch(
        numbers=numeros_grandes,
        content=mensaje,
        batch_size=10000
    )

    print(f"\n📊 Resultados por lote:")
    for lote in resultados:
        result = lote['respuesta']
        estado = "✅" if result.get('code') == 0 else "❌"
        print(
            f"{estado} Lote {lote['lote']}: "
            f"{lote['numeros_enviados']} números - "
            f"ID: {result.get('id')}"
        )
        if result.get('code') == 0:
            stats.add_sent(lote['numeros_enviados'])
        else:
            stats.add_failed(lote['numeros_enviados'])

    stats.print_summary()


def example_5_get_report():
    """Ejemplo 5: Obtener reporte de SMS"""
    print_separator("📋 EJEMPLO 5: OBTENER REPORTE DE ENTREGA")

    api = TrafficLinkAPI()

    # Estos son IDs de ejemplo - deberían venir de un envío anterior
    ids_para_consultar = ["ID_SMS_123", "ID_SMS_124"]

    print(f"\n🔍 Consultando reportes para IDs:")
    for id_ in ids_para_consultar:
        print(f"   • {id_}")

    print(f"\n⏳ Obteniendo reportes...")
    report = api.get_report(ids_para_consultar)

    print(f"\nRespuesta:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if report.get('code') == 0:
        print(f"\n✅ Reportes obtenidos:")
        details = report.get('detail', [])
        for detail in details:
            status_emoji = "✅" if detail.get('status') == 'delivery_success' else "❌"
            print(
                f"{status_emoji} {detail.get('number')}: "
                f"{detail.get('status')}"
            )


def example_6_receive_sms():
    """Ejemplo 6: Recibir SMS entrantes"""
    print_separator("📨 EJEMPLO 6: RECIBIR SMS ENTRANTES")

    api = TrafficLinkAPI()

    print(f"\n📥 Consultando SMS entrantes...")
    sms_data = api.get_incoming_sms(limit=50)

    print(f"\nRespuesta:")
    print(json.dumps(sms_data, indent=2, ensure_ascii=False))

    if sms_data.get('code') == 0:
        messages = sms_data.get('data', [])
        print(f"\n📨 SMS recibidos: {len(messages)}")
        for msg in messages[:5]:  # Mostrar primeros 5
            print(
                f"   De: {msg.get('sender')} | "
                f"Contenido: {msg.get('content')[:50]}..."
            )


def example_7_create_scheduled_task():
    """Ejemplo 7: Crear tarea programada"""
    print_separator("⏰ EJEMPLO 7: CREAR TAREA PROGRAMADA")

    api = TrafficLinkAPI()

    from datetime import datetime, timedelta

    # Programar para mañana a las 10:00 AM
    mañana = datetime.now() + timedelta(days=1)
    sendtime = mañana.strftime("%Y%m%d100000")

    print(f"\n📅 Tarea programada para: {sendtime}")
    print(f"   (Mañana a las 10:00 AM)")

    numero = "3001234567"
    mensaje = "Este es un mensaje programado para mañana 📅"

    print(f"\n📝 Creando tarea...")
    task = api.create_sms_task(
        task_type=1,  # Tarea programada
        numbers=[numero],
        content=mensaje,
        sendtime=sendtime
    )

    print(f"\nRespuesta:")
    print(json.dumps(task, indent=2, ensure_ascii=False))

    if task.get('code') == 0:
        print(f"\n✅ Tarea creada exitosamente")
        print(f"   ID: {task.get('id')}")
    else:
        print(f"\n❌ Error: {task.get('error_message')}")


def example_8_data_storage():
    """Ejemplo 8: Usar almacenamiento de datos"""
    print_separator("💾 EJEMPLO 8: ALMACENAMIENTO DE DATOS")

    storage = DataStorage()

    # Crear cuenta
    account = Account(
        account="demo@traffilink",
        balance=1000.00,
        gift_balance=50.00
    )
    storage.set_account(account)

    print(f"\n👤 Cuenta configurada:")
    print(f"   {account}")

    # Crear SMS
    sms = SMS(
        id="SMS_001",
        numbers=["3001234567", "3007654321"],
        content="Mensaje de prueba",
        status=SMSStatus.SENT
    )
    storage.add_sms(sms)

    print(f"\n📱 SMS agregado:")
    print(f"   {sms}")

    # Ver estadísticas
    stats = storage.get_statistics()
    print(f"\n📊 Estadísticas:")
    print(f"   Total SMS: {stats['total_sms_messages']}")
    print(f"   Enviados: {stats['sent_messages']}")
    print(f"   Fallidos: {stats['failed_messages']}")


def main():
    """Ejecutar todos los ejemplos"""
    print("="*60)
    print("🚀 EJEMPLOS DE USO - TRAFFILINK API")
    print("="*60)

    print("\n⚠️  NOTA: Estos ejemplos usan números y IDs ficticios.")
    print("Para usar con datos reales, reemplaza los valores.\n")

    # Menú interactivo
    ejemplos = {
        "1": ("Obtener Balance", example_1_get_balance),
        "2": ("Enviar SMS Único", example_2_send_single_sms),
        "3": ("Enviar a Múltiples Números", example_3_send_multiple_sms),
        "4": ("Enviar en Lotes Grandes", example_4_send_batch),
        "5": ("Obtener Reporte", example_5_get_report),
        "6": ("Recibir SMS Entrantes", example_6_receive_sms),
        "7": ("Crear Tarea Programada", example_7_create_scheduled_task),
        "8": ("Usar Almacenamiento de Datos", example_8_data_storage),
        "9": ("Ejecutar Todos", None),
        "0": ("Salir", None),
    }

    while True:
        print("\n" + "="*60)
        print("📋 MENÚ DE EJEMPLOS")
        print("="*60)
        for key, (descripcion, _) in ejemplos.items():
            print(f"  {key}. {descripcion}")

        opcion = input("\n👉 Selecciona un ejemplo (0-9): ").strip()

        if opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
        elif opcion == "9":
            # Ejecutar todos
            print("\n⚙️  Ejecutando todos los ejemplos...")
            try:
                example_1_get_balance()
                example_8_data_storage()
                print("\n✅ Ejemplos completados")
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
        elif opcion in ejemplos and ejemplos[opcion][1]:
            try:
                ejemplos[opcion][1]()
            except Exception as e:
                print(f"\n❌ Error al ejecutar: {str(e)}")
        else:
            print("❌ Opción inválida")


if __name__ == "__main__":
    main()
