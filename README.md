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

⚠️ **IMPORTANTE**: NO copies las comillas ``` cuando pegues los comandos en Cloud Shell.

```bash
# Configurar suscripción (reemplaza <TU_SUBSCRIPTION_ID> con tu ID real)
az account set --subscription "<TU_SUBSCRIPTION_ID>"

# Verificar suscripción activa
az account show --query name -o tsv
```

### 2. Definir Variables de Entorno

**¿Qué hace este paso?** Definimos nombres únicos para nuestros recursos usando variables. Esto evita conflictos con otros estudiantes y hace los comandos más fáciles de leer.

```bash
# Variables del laboratorio
RG="rg-webapp-mi-lab"
LOC="canadacentral"
PLAN="plan-webapp-mi-lab"
APP="webapp-mi-lab-$RANDOM"
SA="st${RANDOM}milab"

# Mostrar variables para verificar (IMPORTANTE: apunta estos valores)
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

# Dar permiso a nuestra app para LEER archivos (principio de menor privilegio)
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Reader" \
  --scope $STORAGE_ID
```

### 6. Crear Contenedor y Blob de Prueba

**¿Qué hace este paso?** Creamos una "carpeta" (contenedor) en nuestro Storage Account y subimos un archivo de texto que nuestra app podrá leer para demostrar que Managed Identity funciona.

```bash
# Crear contenedor (como una carpeta en el storage)
az storage container create \
  --name "demo" \
  --account-name $SA \
  --auth-mode login

# Crear archivo de prueba y subirlo
echo "¡Hola desde Azure Storage con Managed Identity!" > demo.txt
az storage blob upload \
  --file demo.txt \
  --container-name "demo" \
  --name "mensaje.txt" \
  --account-name $SA \
  --auth-mode key

# Limpiar archivo local
rm demo.txt
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
