from flask import Flask, render_template_string, jsonify
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Template HTML simple
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Azure App Service + Managed Identity Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
        .success { color: #28a745; background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .error { color: #dc3545; background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .info { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .code { background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; margin: 10px 0; }
        button { background: #0066cc; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0052a3; }
    </style>
    <script>
        async function testStorage() {
            try {
                const response = await fetch('/test-storage');
                const data = await response.json();
                document.getElementById('result').innerHTML = data.success ? 
                    `<div class="success"><strong>✅ Éxito:</strong> ${data.message}</div>` :
                    `<div class="error"><strong>❌ Error:</strong> ${data.error}</div>`;
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    `<div class="error"><strong>❌ Error:</strong> ${error.message}</div>`;
            }
        }
        
        async function checkIdentity() {
            try {
                const response = await fetch('/check-identity');
                const data = await response.json();
                document.getElementById('identity-result').innerHTML = 
                    `<div class="info"><strong>🔐 Managed Identity:</strong> ${data.status}</div>`;
            } catch (error) {
                document.getElementById('identity-result').innerHTML = 
                    `<div class="error"><strong>❌ Error:</strong> ${error.message}</div>`;
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h1 class="header">🚀 Azure App Service + Managed Identity</h1>
        
        <div class="info">
            <strong>📋 Este laboratorio demuestra:</strong>
            <ul>
                <li>Autenticación sin secrets usando Managed Identity</li>
                <li>Acceso seguro a Azure Storage</li>
                <li>Uso de DefaultAzureCredential</li>
                <li>Mejores prácticas de seguridad en Azure</li>
            </ul>
        </div>
        
        <h2>🧪 Pruebas</h2>
        
        <button onclick="checkIdentity()">🔐 Verificar Managed Identity</button>
        <div id="identity-result"></div>
        
        <button onclick="testStorage()">📦 Probar Acceso a Storage</button>
        <div id="result"></div>
        
        <h2>📊 Información del Sistema</h2>
        <div class="code">
            <strong>Storage Account:</strong> {{ storage_account or 'No configurado' }}<br>
            <strong>Python Version:</strong> {{ python_version }}<br>
            <strong>Azure Identity Version:</strong> {{ azure_identity_version }}<br>
            <strong>Timestamp:</strong> {{ timestamp }}
        </div>
        
        <h2>🔧 Variables de Entorno</h2>
        <div class="code">
            {% for key, value in env_vars.items() %}
            <strong>{{ key }}:</strong> {{ value }}<br>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def home():
    import sys
    import azure.identity
    from datetime import datetime

    # Información del sistema
    storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT')
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    azure_identity_version = azure.identity.__version__
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

    # Variables de entorno relevantes (filtradas por seguridad)
    env_vars = {
        'AZURE_STORAGE_ACCOUNT': storage_account,
        'WEBSITE_SITE_NAME': os.environ.get('WEBSITE_SITE_NAME', 'Local'),
        'WEBSITE_RESOURCE_GROUP': os.environ.get('WEBSITE_RESOURCE_GROUP', 'Local'),
        'WEBSITE_SKU': os.environ.get('WEBSITE_SKU', 'Local')
    }

    return render_template_string(HTML_TEMPLATE,
                                  storage_account=storage_account,
                                  python_version=python_version,
                                  azure_identity_version=azure_identity_version,
                                  timestamp=timestamp,
                                  env_vars=env_vars)


@app.route('/check-identity')
def check_identity():
    """Verificar si Managed Identity está disponible"""
    try:
        credential = DefaultAzureCredential()
        # Intentar obtener un token para verificar la identidad
        token = credential.get_token("https://storage.azure.com/.default")

        return jsonify({
            'success': True,
            'status': '✅ Managed Identity está funcionando correctamente',
            'token_type': 'Bearer'
        })
    except Exception as e:
        logger.error(f"Error verificando Managed Identity: {str(e)}")
        return jsonify({
            'success': False,
            'status': f'❌ Error: {str(e)}'
        })


@app.route('/test-storage')
def test_storage():
    """Probar acceso a Azure Storage usando Managed Identity"""
    try:
        # Obtener el nombre del Storage Account
        storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT')
        if not storage_account:
            return jsonify({
                'success': False,
                'error': 'AZURE_STORAGE_ACCOUNT no está configurado'
            })

        # Crear cliente de Storage usando Managed Identity
        account_url = f"https://{storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url, credential=credential)

        # Intentar leer el blob de demostración
        container_name = "demo"
        blob_name = "mensaje.txt"

        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name)

        # Leer el contenido del blob
        blob_content = blob_client.download_blob().readall().decode('utf-8')

        logger.info(f"Blob leído exitosamente: {blob_content}")

        return jsonify({
            'success': True,
            'message': f'Contenido del blob: {blob_content}',
            'storage_account': storage_account,
            'container': container_name,
            'blob': blob_name
        })

    except Exception as e:
        logger.error(f"Error accediendo a Storage: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/health')
def health():
    """Endpoint de salud para monitoreo"""
    return jsonify({
        'status': 'healthy',
        'timestamp': os.popen('date').read().strip()
    })


if __name__ == '__main__':
    # Configuración para App Service
    port = int(os.environ.get('PORT', 8000))  # Cambiar a 8000
    app.run(host='0.0.0.0', port=port, debug=False)
