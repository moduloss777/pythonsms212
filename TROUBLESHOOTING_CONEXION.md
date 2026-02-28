# 🔧 Troubleshooting: Error de Autenticación en Render.com

## El Problema

Cuando intentas hacer login en Render.com, recibes "Autenticación fallida", pero funciona localmente.

```
❌ No se pudo iniciar sesión: ❌ Autenticación fallida
```

## Causa Probable

**Render.com no puede conectarse al servidor de Traffilink en `47.236.91.242:20003`**

Esto sucede cuando:
- El servidor está en una red privada/local
- Hay un firewall bloqueando conexiones externas
- La IP requiere estar en una whitelist
- Render.com está en una ubicación geográfica bloqueada

## Solución

### Paso 1: Verificar si la IP es pública o privada

```bash
# En tu computadora local
ping 47.236.91.242
nslookup 47.236.91.242
```

Si responde, probablemente es pública. Si no responde, es privada.

### Paso 2: Revisar los logs mejorados en Render.com

He agregado logging más detallado. Ve a:

1. Render.com Dashboard
2. Tu servicio "goleador-sms-api"
3. Pestaña "Logs"
4. Intenta hacer login
5. Busca mensajes como:
   - `ERROR DE CONEXIÓN: No se puede conectar a...`
   - `TIMEOUT: El servidor no respondió...`
   - `Posibles causas: IP/puerto incorrectos...`

### Paso 3: Soluciones según el error

#### Si ves "ERROR DE CONEXIÓN"
El servidor probablemente está en una red privada y Render.com no puede alcanzarlo.

**Soluciones:**
1. Contacta a tu proveedor de Traffilink
2. Pregunta si la IP es pública y accesible desde internet
3. Pregunta si necesitas autorizar la IP de Render.com
4. Pregunta si hay una alternativa de API pública

#### Si ves "TIMEOUT"
El servidor está lento o no responde. Aumenta el timeout en config.py.

#### Si ves error de autenticación (code: -1)
La IP se conecta pero las credenciales son rechazadas.
- Verifica que ACCOUNT y PASSWORD sean exactas
- Contacta al proveedor para confirmar credenciales

### Paso 4: Preguntas para tu proveedor de Traffilink

Envía estas preguntas a tu proveedor:

```
1. ¿La IP 47.236.91.242 es pública y accesible desde internet?
2. ¿Hay restricciones de IP whitelist?
3. Si necesito conectar desde Render.com, ¿qué IP debo autorizar?
4. ¿Hay un endpoint público/alternativo para la API?
5. ¿Las credenciales (0152C274 / G2o0jRnm) son válidas?
6. ¿Requiere encriptación SSL/TLS (https en lugar de http)?
```

## Alternativas Temporales

Mientras resuelves el acceso:

### Opción A: Local Development
```bash
# En tu computadora
python app.py
# Luego accede a http://localhost:5000/login
```

### Opción B: Usar Variable de Entorno para URL diferente

Si tienes un endpoint alternativo:

1. En Render.com Dashboard
2. Settings → Environment Variables
3. Agrega: `TRAFFILINK_BASE_URL=https://tu-nuevo-endpoint`
4. Modifica config.py para usar os.getenv():

```python
TRAFFILINK_BASE_URL = os.getenv(
    "TRAFFILINK_BASE_URL",
    "http://47.236.91.242:20003"
)
```

## Verificación Rápida

Crea un archivo `test_conexion.py`:

```python
import requests
import sys

url = "http://47.236.91.242:20003/getbalance"
params = {
    "account": "0152C274",
    "password": "G2o0jRnm"
}

try:
    print(f"Intentando conectar a: {url}")
    response = requests.get(url, params=params, timeout=5)
    print(f"✅ Conectado! Status: {response.status_code}")
    print(f"Respuesta: {response.text}")
except requests.exceptions.ConnectionError:
    print("❌ No se puede conectar (ERROR DE CONEXIÓN)")
    print("   Probablemente la IP es privada o está bloqueada")
except requests.exceptions.Timeout:
    print("❌ Timeout (servidor no responde en 5 segundos)")
except Exception as e:
    print(f"❌ Error: {str(e)}")
```

Ejecuta:
```bash
python test_conexion.py
```

## Pasos Siguientes

1. **Agrega logging mejorado** (ya hecho ✅)
2. **Haz commit y push:**
   ```bash
   git add traffilink_api.py
   git commit -m "Improve: Add detailed error logging for connection issues"
   git push origin main
   ```
3. **Espera a que Render.com redeploy** (2-5 minutos)
4. **Intenta login y revisa logs**
5. **Cópiame los errores exactos**

---

**Próxima acción:**
Completa los pasos arriba y comparte los logs que ves en Render.com.
Así sabremos exactamente cuál es el problema. 🔍
