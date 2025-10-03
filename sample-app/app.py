from flask import Flask, render_template_string, jsonify, request, redirect, url_for
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Template HTML para el FTP web
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Azure Storage FTP - Subir Imágenes de Errores</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
        .success { color: #28a745; background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .error { color: #dc3545; background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .info { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .code { background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; margin: 10px 0; }
        .upload-section { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .file-list { margin: 20px 0; }
        .file-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee; }
        .file-item img { max-width: 100px; max-height: 100px; object-fit: cover; cursor: pointer; }
        .file-actions { display: flex; gap: 10px; }
        button { background: #0066cc; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0052a3; }
        .delete-btn { background: #dc3545; }
        .delete-btn:hover { background: #c82333; }
        .view-btn { background: #28a745; }
        .view-btn:hover { background: #218838; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.9); }
        .modal-content { margin: auto; display: block; width: 80%; max-width: 700px; }
        .close { position: absolute; top: 15px; right: 35px; color: #f1f1f1; font-size: 40px; font-weight: bold; cursor: pointer; }
        .close:hover { color: #bbb; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">📸 Azure Storage FTP - Subir Imágenes de Errores</h1>
        
        <div class="info">
            <strong>📋 Este laboratorio permite:</strong>
            <ul>
                <li>🔐 Autenticación segura usando Managed Identity</li>
                <li>📤 Subir imágenes de errores (PNG, JPG, GIF)</li>
                <li>📂 Listar archivos almacenados</li>
                <li>👁️ Visualizar imágenes</li>
                <li>🗑️ Borrar archivos (importante para datos públicos)</li>
            </ul>
        </div>

        <!-- Sección de subida -->
        <div class="upload-section">
            <h2>📤 Subir Nueva Imagen</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept="image/*" required>
                <button type="submit">📤 Subir Imagen</button>
            </form>
        </div>

        <!-- Lista de archivos -->
        <div class="file-list">
            <h2>📂 Archivos Subidos</h2>
            <button onclick="loadFiles()">🔄 Actualizar Lista</button>
            <div id="files-container">
                <p>Haz clic en "Actualizar Lista" para ver los archivos...</p>
            </div>
        </div>
        
        <h2>📊 Información del Sistema</h2>
        <div class="code">
            <strong>Storage Account:</strong> {{ storage_account or 'No configurado' }}<br>
            <strong>Container:</strong> uploads<br>
            <strong>Timestamp:</strong> {{ timestamp }}
        </div>
    </div>

    <!-- Modal para ver imágenes -->
    <div id="imageModal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>

    <script>
        async function loadFiles() {
            try {
                const response = await fetch('/list-files');
                const data = await response.json();
                
                if (data.success) {
                    const container = document.getElementById('files-container');
                    if (data.files.length === 0) {
                        container.innerHTML = '<p>No hay archivos subidos aún.</p>';
                    } else {
                        container.innerHTML = data.files.map(file => `
                            <div class="file-item">
                                <div>
                                    <strong>${file.name}</strong><br>
                                    <small>Tamaño: ${file.size} bytes | Subido: ${file.last_modified}</small>
                                </div>
                                <div class="file-actions">
                                    <button class="view-btn" onclick="viewImage('${file.name}')">👁️ Ver</button>
                                    <button class="delete-btn" onclick="deleteFile('${file.name}')">🗑️ Borrar</button>
                                </div>
                            </div>
                        `).join('');
                    }
                } else {
                    document.getElementById('files-container').innerHTML = 
                        `<div class="error">Error: ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('files-container').innerHTML = 
                    `<div class="error">Error: ${error.message}</div>`;
            }
        }

        async function deleteFile(filename) {
            if (!confirm(`¿Estás seguro de que quieres borrar "${filename}"?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/delete/${filename}`, { method: 'DELETE' });
                const data = await response.json();
                
                if (data.success) {
                    alert('Archivo borrado exitosamente');
                    loadFiles(); // Recargar lista
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        }

        function viewImage(filename) {
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            modal.style.display = 'block';
            modalImg.src = `/view/${filename}`;
        }

        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }

        // Cerrar modal al hacer clic fuera de la imagen
        window.onclick = function(event) {
            const modal = document.getElementById('imageModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    from datetime import datetime

    # Información del sistema
    storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

    return render_template_string(HTML_TEMPLATE,
                                  storage_account=storage_account,
                                  timestamp=timestamp)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Subir archivo a Azure Storage"""
    try:
        if 'file' not in request.files:
            return redirect(url_for('home'))

        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('home'))

        # Validar tipo de archivo
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return redirect(url_for('home'))

        # Obtener cliente de Storage
        storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT')
        if not storage_account:
            return redirect(url_for('home'))

        account_url = f"https://{storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url, credential=credential)

        # Crear contenedor si no existe
        container_name = "uploads"
        try:
            blob_service_client.create_container(container_name)
        except Exception:
            pass  # Container ya existe

        # Subir archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob_name = f"{timestamp}_{file.filename}"
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name)

        blob_client.upload_blob(file.read(), overwrite=True)
        logger.info(f"Archivo subido: {blob_name}")

        return redirect(url_for('home'))

    except Exception as e:
        logger.error(f"Error subiendo archivo: {str(e)}")
        return redirect(url_for('home'))


@app.route('/list-files')
def list_files():
    """Listar archivos en Azure Storage"""
    try:
        storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT')
        if not storage_account:
            return jsonify({'success': False, 'error': 'Storage account no configurado'})

        account_url = f"https://{storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url, credential=credential)

        container_client = blob_service_client.get_container_client("uploads")

        files = []
        for blob in container_client.list_blobs():
            files.append({
                'name': blob.name,
                'size': blob.size,
                'last_modified': blob.last_modified.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify({'success': True, 'files': files})

    except Exception as e:
        logger.error(f"Error listando archivos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/view/<filename>')
def view_file(filename):
    """Ver archivo desde Azure Storage"""
    try:
        storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT')
        if not storage_account:
            return "Storage account no configurado", 404

        account_url = f"https://{storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url, credential=credential)

        blob_client = blob_service_client.get_blob_client(
            container="uploads", blob=filename)
        blob_data = blob_client.download_blob().readall()

        # Determinar tipo de contenido
        file_ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }
        content_type = content_types.get(file_ext, 'application/octet-stream')

        from flask import Response
        return Response(blob_data, content_type=content_type)

    except Exception as e:
        logger.error(f"Error viendo archivo: {str(e)}")
        return "Archivo no encontrado", 404


@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Borrar archivo de Azure Storage"""
    try:
        storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT')
        if not storage_account:
            return jsonify({'success': False, 'error': 'Storage account no configurado'})

        account_url = f"https://{storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url, credential=credential)

        blob_client = blob_service_client.get_blob_client(
            container="uploads", blob=filename)
        blob_client.delete_blob()

        logger.info(f"Archivo borrado: {filename}")
        return jsonify({'success': True, 'message': f'Archivo {filename} borrado exitosamente'})

    except Exception as e:
        logger.error(f"Error borrando archivo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/health')
def health():
    """Endpoint de salud para monitoreo"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    })


if __name__ == '__main__':
    # Configuración para App Service
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
