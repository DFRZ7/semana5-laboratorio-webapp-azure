# Azure App Service con Flask y Managed Identity - Laboratorio

## 🎯 Objetivo del Laboratorio

Aprende a desplegar una aplicación Flask en Azure App Service utilizando **Managed Identity** para autenticación segura sin secrets o connection strings.

## 📋 Prerrequisitos

- Suscripción de Azure activa
- Permisos para crear recursos y asignar roles
- Acceso a Azure Cloud Shell (Bash)

## 🔒 Nota de Seguridad

⚠️ **IMPORTANTE**: Este laboratorio es para fines educativos. Los ejemplos de passwords y configuraciones NO deben usarse en producción. Siempre usa:

- Passwords seguros generados automáticamente
- Principio de menor privilegio
- Rotación regular de credenciales

## 🚀 Pasos del Laboratorio

### 1. Configuración Inicial

**¿Qué hace este paso?** Configuramos nuestra suscripción de Azure y verificamos que tenemos acceso.

Abre Azure Cloud Shell desde el portal de Azure y ejecuta:

> ⚠️ **MUY IMPORTANTE**:
>
> - Cuando abras Azure Cloud Shell, **SELECCIONA "Bash"** en lugar de PowerShell
> - Si ves "PS" en el prompt, cambia a Bash - todos los comandos están escritos para Bash
> - NO copies las comillas ``` cuando pegues los comandos en Cloud Shell

```bash
# Configurar suscripción (reemplaza <TU_SUBSCRIPTION_ID> con tu ID real)
az account set --subscription "<TU_SUBSCRIPTION_ID>"

# Verificar suscripción activa
az account show --query name -o tsv
```

### 2. Definir Variables de Entorno

**¿Qué hace este paso?** Generamos UN número aleatorio único y lo usamos para todos nuestros recursos. Esto garantiza que cada estudiante tenga nombres únicos pero coherentes, evitando conflictos cuando múltiples personas ejecuten el laboratorio simultáneamente.

```bash
# Generar un ID único para este laboratorio
RANDOM_ID=$RANDOM

# Variables del laboratorio (todas usando el mismo ID único)
RG="rg-webapp-mi-lab-$RANDOM_ID"
LOC="canadacentral"
PLAN="plan-webapp-mi-lab-$RANDOM_ID"
APP="webapp-mi-lab-$RANDOM_ID"
SA="st${RANDOM_ID}milab"

# Mostrar variables para verificar (IMPORTANTE: apunta estos valores)
echo "Random ID compartido: $RANDOM_ID"
echo "Resource Group: $RG"
echo "Location: $LOC"
echo "App Service Plan: $PLAN"
echo "Web App: $APP"
echo "Storage Account: $SA"
```

### 3. Crear Recursos Base

**¿Qué hace este paso?** Creamos la infraestructura básica: un grupo de recursos para organizar todo, un plan de App Service (la "máquina virtual" donde correrá nuestra app), y la Web App misma.

```bash
# Crear grupo de recursos (contenedor lógico para todos nuestros recursos)
az group create --name $RG --location $LOC

# Crear App Service Plan (define el tamaño y capacidad del servidor)
az appservice plan create \
  --name $PLAN \
  --resource-group $RG \
  --sku B1 \
  --is-linux

# Crear Web App (nuestra aplicación Flask)
az webapp create \
  --name $APP \
  --resource-group $RG \
  --plan $PLAN \
  --runtime "PYTHON:3.10"
```

### 4. Habilitar Managed Identity

**¿Qué hace este paso?** Activamos la "identidad administrada" de nuestra Web App. Esto es como darle una "cédula de identidad" a nuestra aplicación para que pueda autenticarse automáticamente con otros servicios de Azure sin necesidad de passwords.

```bash
# Asignar identidad administrada a la Web App
az webapp identity assign \
  --resource-group $RG \
  --name $APP

# Obtener el Principal ID (el "número de cédula" de nuestra app)
PRINCIPAL_ID=$(az webapp identity show \
  --resource-group $RG \
  --name $APP \
  --query principalId \
  --output tsv)

echo "Principal ID: $PRINCIPAL_ID"
```

### 5. Crear Azure Storage Account

**¿Qué hace este paso?** Creamos un "disco duro en la nube" (Storage Account) donde nuestra app guardará archivos. Luego le damos permiso a nuestra app para que pueda leer archivos de ahí.

```bash
# Crear Storage Account (almacenamiento en la nube)
az storage account create \
  --name $SA \
  --resource-group $RG \
  --location $LOC \
  --sku Standard_LRS

# Obtener el ID único del Storage Account
STORAGE_ID=$(az storage account show \
  --name $SA \
  --resource-group $RG \
  --query id \
  --output tsv)

# Dar permisos a nuestra app para LEER y ESCRIBIR archivos (necesario para el FTP)
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID
```

### 6. Crear Contenedor para Uploads

**¿Qué hace este paso?** Creamos un contenedor llamado "uploads" donde nuestra aplicación FTP web almacenará las imágenes que suban los usuarios. Este contenedor se creará automáticamente la primera vez que alguien suba un archivo, pero también podemos crearlo manualmente.

```bash
# Crear contenedor para uploads (la app lo creará automáticamente si no existe)
az storage container create \
  --name "uploads" \
  --account-name $SA \
  --auth-mode login

echo "✅ Contenedor 'uploads' creado para el FTP web"
```

### 7. Configurar Variables de Aplicación

**¿Qué hace este paso?** Le decimos a nuestra Web App cuál es el nombre de nuestro Storage Account. La app leerá esta configuración cuando se ejecute.

```bash
# Configurar el nombre del Storage Account como variable de entorno
az webapp config appsettings set \
  --resource-group $RG \
  --name $APP \
  --settings AZURE_STORAGE_ACCOUNT=$SA
```

### 8. Descargar y Preparar el Código

**¿Qué hace este paso?** Descargamos el código de la aplicación Flask desde GitHub. Esta app ya está programada para usar Managed Identity.

```bash
# Limpiar cualquier descarga anterior y descargar código actualizado
rm -rf semana5-laboratorio-webapp-azure
git clone https://github.com/DFRZ7/semana5-laboratorio-webapp-azure.git
cd semana5-laboratorio-webapp-azure/sample-app
```

### 9. Configurar App Service

**¿Qué hace este paso?** Le decimos a Azure cómo ejecutar nuestra aplicación Flask usando el archivo startup.sh que viene incluido en el código.

```bash
# Configurar archivo de inicio para que App Service sepa cómo ejecutar nuestra app
az webapp config set \
  --resource-group $RG \
  --name $APP \
  --startup-file "startup.sh"
```

### 10. Desplegar la Aplicación

**¿Qué hace este paso?** Empaquetamos nuestro código en un archivo ZIP y lo subimos a Azure. Azure instalará las dependencias y ejecutará nuestra app.

```bash
# Crear archivo ZIP con todos los archivos de la aplicación
zip -r ../app.zip .
cd ..

# Desplegar a Azure (esto puede tomar 2-3 minutos)
az webapp deployment source config-zip \
  --resource-group $RG \
  --name $APP \
  --src app.zip
```

⏱️ **NOTA**: El despliegue puede tardar 2-3 minutos. Azure está instalando Python, las dependencias y configurando todo.

### 11. Verificar el Despliegue

```bash
# Obtener la URL de la aplicación
az webapp show \
  --resource-group $RG \
  --name $APP \
  --query defaultHostName \
  --output tsv

# Abrir la aplicación en el navegador
az webapp browse \
  --resource-group $RG \
  --name $APP
```

### 12. Monitorear la Aplicación

```bash
# Ver logs en tiempo real
az webapp log tail \
  --resource-group $RG \
  --name $APP

# Ver configuración de la aplicación
az webapp config show \
  --resource-group $RG \
  --name $APP
```

### 13. Limpieza de Recursos

```bash
# ⚠️ CUIDADO: Esto eliminará TODOS los recursos
az group delete \
  --name $RG \
  --yes \
  --no-wait
```

## 🔍 Puntos Clave del Laboratorio

1. **Managed Identity**: No hay secrets en el código
2. **DefaultAzureCredential**: Autenticación automática
3. **Principio de menor privilegio**: Solo permisos necesarios
4. **Monitoreo**: Logs y métricas integradas

## 🎯 RETO: Personaliza tu Aplicación

¡Ahora que tu aplicación funciona perfectamente, es hora de personalizarla! Este reto te ayudará a entender cómo actualizar aplicaciones en Azure y mostrar tu creatividad a tus compañeros.

### 🎨 Ideas de Personalización

**Cambios Fáciles (HTML/CSS):**

- Cambiar el título de la página
- Modificar los colores del tema
- Agregar tu nombre o equipo
- Cambiar los emojis por otros
- Personalizar los mensajes de texto

**Cambios Avanzados (Python):**

- Agregar validación de tamaño de archivo
- Mostrar información adicional de los archivos
- Cambiar el formato de timestamp

### 🔧 Cómo Hacer los Cambios

**¿Qué hace este paso?** Vamos a modificar la aplicación localmente y luego actualizarla en Azure usando el mismo proceso de despliegue.

```bash
# 1. Ir al directorio de la aplicación
cd sample-app

# 2. Editar el archivo app.py (puedes usar nano, vim, o descargar/editar)
nano app.py

# 3. Hacer tus cambios personalizados (ver ejemplos abajo)

# 4. Crear el ZIP actualizado
zip -r ../app.zip . -x "*.pyc" "__pycache__/*"

# 5. Volver al directorio principal
cd ..

# 6. Redesplegar la aplicación (¡usa las mismas variables!)
az webapp deployment source config-zip \
  --resource-group $RG \
  --name $APP \
  --src app.zip

# 7. Ver los logs durante el despliegue
az webapp log tail --name $APP --resource-group $RG
```

### 💡 Ejemplos de Personalización

**Cambiar el título y agregar tu nombre:**

```python
# Busca esta línea en app.py:
<title>Azure Storage FTP - Subir Imágenes de Errores</title>

# Cámbiala por:
<title>🌟 FTP de [TU NOMBRE] - Mi Azure Lab</title>
```

**Cambiar el color del tema:**

```css
#Busca esta línea en el CSS: .header {
  color: #0066cc;
  border-bottom: 2px solid #0066cc;
  padding-bottom: 10px;
}

#Cámbiala por tu color favorito: .header {
  color: #ff6b35;
  border-bottom: 2px solid #ff6b35;
  padding-bottom: 10px;
}
```

**Personalizar el mensaje de bienvenida:**

```html
# Busca:
<h1 class="header">📸 Azure Storage FTP - Subir Imágenes de Errores</h1>

# Cámbialo por:
<h1 class="header">🚀 [TU NOMBRE]'s Azure Lab - ¡Funcionando perfectamente!</h1>
```

**Cambiar los botones:**

```css
#Busca: button {
  background: #0066cc;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin: 5px;
}

#Prueba con: button {
  background: linear-gradient(45deg, #ff6b35, #f7931e);
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin: 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
```

### 🏆 Presenta tu Trabajo

1. **Toma una captura** de tu aplicación personalizada
2. **Comparte la URL** con tus compañeros: `https://webapp-mi-lab-[TU-NUMERO].azurewebsites.net`
3. **Explica qué cambiaste** y por qué
4. **Muestra el proceso** de actualización

### ⏱️ Tiempo de Actualización

- **Redespliegue**: 1-2 minutos
- **Aplicación disponible**: Inmediatamente después del despliegue
- **Tip**: Usa `Ctrl+F5` para refrescar completamente la página

### 🎉 Objetivos del Reto

- ✅ Entender el proceso de actualización de aplicaciones en Azure
- ✅ Experimentar con HTML, CSS y Python
- ✅ Practicar el flujo completo de desarrollo
- ✅ Compartir y presentar tu trabajo

**¡Diviértete personalizando tu aplicación! 🎨**

---

## 📚 Recursos Adicionales

- [Managed Identity en App Service](https://docs.microsoft.com/azure/app-service/overview-managed-identity)
- [Azure SDK para Python](https://docs.microsoft.com/python/api/overview/azure/)
- [DefaultAzureCredential](https://docs.microsoft.com/python/api/azure-identity/azure.identity.defaultazurecredential)

## 🆘 Solución de Problemas

### Error: "No se puede autenticar"

- Verificar que Managed Identity esté habilitada
- Confirmar que los roles estén asignados correctamente

### Error: "Aplicación no inicia"

- Revisar logs con `az webapp log tail`
- Verificar que `requirements.txt` esté completo

### Error: "No se encuentra el Storage Account"

- Confirmar que la variable `AZURE_STORAGE_ACCOUNT` esté configurada
- Verificar que el Storage Account exista en el mismo Resource Group

---

**¡Felicidades! Has completado el laboratorio de Azure App Service con Managed Identity** 🎉
