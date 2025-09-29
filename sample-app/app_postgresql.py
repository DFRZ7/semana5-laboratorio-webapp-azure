# EJEMPLO ALTERNATIVO: Azure App Service con PostgreSQL Flexible Server
# Este archivo demuestra cómo usar Managed Identity con PostgreSQL

from flask import Flask, render_template_string, jsonify
from azure.identity import DefaultAzureCredential
import psycopg2
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Template HTML para PostgreSQL demo
HTML_TEMPLATE_PG = """
<!DOCTYPE html>
<html>
<head>
    <title>Azure App Service + PostgreSQL + Managed Identity</title>
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
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
    <script>
        async function testDatabase() {
            try {
                const response = await fetch('/test-database');
                const data = await response.json();
                document.getElementById('result').innerHTML = data.success ? 
                    `<div class="success"><strong>✅ Éxito:</strong> ${data.message}</div>` :
                    `<div class="error"><strong>❌ Error:</strong> ${data.error}</div>`;
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    `<div class="error"><strong>❌ Error:</strong> ${error.message}</div>`;
            }
        }
        
        async function getUsers() {
            try {
                const response = await fetch('/get-users');
                const data = await response.json();
                if (data.success) {
                    let tableHtml = '<table><tr><th>ID</th><th>Name</th><th>Email</th><th>Created</th></tr>';
                    data.users.forEach(user => {
                        tableHtml += `<tr><td>${user.id}</td><td>${user.name}</td><td>${user.email}</td><td>${user.created_at}</td></tr>`;
                    });
                    tableHtml += '</table>';
                    document.getElementById('users-result').innerHTML = 
                        `<div class="success"><strong>📊 Usuarios en la base de datos:</strong><br>${tableHtml}</div>`;
                } else {
                    document.getElementById('users-result').innerHTML = 
                        `<div class="error"><strong>❌ Error:</strong> ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('users-result').innerHTML = 
                    `<div class="error"><strong>❌ Error:</strong> ${error.message}</div>`;
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h1 class="header">🐘 Azure App Service + PostgreSQL + Managed Identity</h1>
        
        <div class="info">
            <strong>📋 Este ejemplo demuestra:</strong>
            <ul>
                <li>Conexión a PostgreSQL Flexible Server usando Managed Identity</li>
                <li>Autenticación Entra ID para base de datos</li>
                <li>Operaciones CRUD básicas</li>
                <li>Mejores prácticas de seguridad para bases de datos</li>
            </ul>
        </div>
        
        <h2>🧪 Pruebas</h2>
        
        <button onclick="testDatabase()">🐘 Probar Conexión a PostgreSQL</button>
        <div id="result"></div>
        
        <button onclick="getUsers()">📊 Obtener Usuarios</button>
        <div id="users-result"></div>
        
        <h2>📊 Información de Configuración</h2>
        <div class="code">
            <strong>PostgreSQL Server:</strong> {{ pg_server or 'No configurado' }}<br>
            <strong>Database:</strong> {{ pg_database or 'No configurado' }}<br>
            <strong>Authentication:</strong> Azure AD (Managed Identity)<br>
            <strong>Timestamp:</strong> {{ timestamp }}
        </div>
    </div>
</body>
</html>
"""


def get_db_connection():
    """Crear conexión a PostgreSQL usando Managed Identity"""
    try:
        # Obtener configuración desde variables de entorno
        pg_server = os.environ.get('AZURE_POSTGRESQL_SERVER')
        pg_database = os.environ.get('AZURE_POSTGRESQL_DATABASE', 'postgres')
        pg_user = os.environ.get('AZURE_POSTGRESQL_USER')

        if not pg_server or not pg_user:
            raise ValueError("Variables de PostgreSQL no configuradas")

        # Obtener token de acceso usando Managed Identity
        credential = DefaultAzureCredential()
        token = credential.get_token(
            "https://ossrdbms-aad.database.windows.net")

        # Crear conexión usando el token como password
        connection = psycopg2.connect(
            host=f"{pg_server}.postgres.database.azure.com",
            database=pg_database,
            user=pg_user,
            password=token.token,
            port=5432,
            sslmode='require'
        )

        return connection

    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL: {str(e)}")
        raise


@app.route('/')
def home():
    from datetime import datetime

    # Información de configuración
    pg_server = os.environ.get('AZURE_POSTGRESQL_SERVER')
    pg_database = os.environ.get('AZURE_POSTGRESQL_DATABASE', 'postgres')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

    return render_template_string(HTML_TEMPLATE_PG,
                                  pg_server=pg_server,
                                  pg_database=pg_database,
                                  timestamp=timestamp)


@app.route('/test-database')
def test_database():
    """Probar conexión a PostgreSQL"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Ejecutar consulta simple
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        logger.info("Conexión a PostgreSQL exitosa")

        return jsonify({
            'success': True,
            'message': f'Conexión exitosa. Versión: {version[:50]}...'
        })

    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/get-users')
def get_users():
    """Obtener usuarios de la tabla demo"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS demo_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Insertar datos de ejemplo si la tabla está vacía
        cursor.execute("SELECT COUNT(*) FROM demo_users;")
        count = cursor.fetchone()[0]

        if count == 0:
            sample_users = [
                ('Juan Pérez', 'juan.perez@example.com'),
                ('María García', 'maria.garcia@example.com'),
                ('Carlos López', 'carlos.lopez@example.com')
            ]

            for name, email in sample_users:
                cursor.execute(
                    "INSERT INTO demo_users (name, email) VALUES (%s, %s);",
                    (name, email)
                )

        # Obtener todos los usuarios
        cursor.execute("""
            SELECT id, name, email, created_at 
            FROM demo_users 
            ORDER BY created_at DESC;
        """)

        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'created_at': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else 'N/A'
            })

        connection.commit()
        cursor.close()
        connection.close()

        logger.info(f"Obtenidos {len(users)} usuarios de PostgreSQL")

        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        })

    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/health')
def health():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'database': 'postgresql',
        'timestamp': os.popen('date').read().strip()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
