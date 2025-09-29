# 🔧 Guía de Solución de Problemas

## 🚨 Errores Comunes y Soluciones

### 1. Error de Autenticación

#### Síntoma

```
DefaultAzureCredential failed to retrieve a token from the included credentials
```

#### Causas Posibles

- Managed Identity no habilitada
- Permisos RBAC insuficientes
- Variables de entorno mal configuradas

#### Solución Paso a Paso

```bash
# 1. Verificar que Managed Identity esté habilitada
az webapp identity show --resource-group $RG --name $APP

# Debe mostrar:
# {
#   "principalId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
#   "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
#   "type": "SystemAssigned"
# }

# 2. Si no está habilitada, habilitarla
az webapp identity assign --resource-group $RG --name $APP

# 3. Verificar asignaciones de rol
PRINCIPAL_ID=$(az webapp identity show -g $RG -n $APP --query principalId -o tsv)
az role assignment list --assignee $PRINCIPAL_ID --output table

# 4. Si no hay asignaciones, crear la necesaria
STORAGE_ID=$(az storage account show -n $SA -g $RG --query id -o tsv)
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Reader" \
  --scope $STORAGE_ID
```

### 2. Error de Storage Account

#### Síntoma

```
AZURE_STORAGE_ACCOUNT no está configurado
```

#### Solución

```bash
# 1. Verificar configuración actual
az webapp config appsettings list --resource-group $RG --name $APP --query "[?name=='AZURE_STORAGE_ACCOUNT']" --output table

# 2. Si no existe, configurarla
az webapp config appsettings set \
  --resource-group $RG \
  --name $APP \
  --settings AZURE_STORAGE_ACCOUNT=$SA

# 3. Verificar que el Storage Account existe
az storage account show --name $SA --resource-group $RG
```

### 3. Error de Contenedor o Blob

#### Síntoma

```
The specified container does not exist
The specified blob does not exist
```

#### Solución

```bash
# 1. Verificar contenedores existentes
az storage container list --account-name $SA --auth-mode login --output table

# 2. Crear contenedor si no existe
az storage container create --name "demo" --account-name $SA --auth-mode login

# 3. Crear blob de prueba
echo "¡Hola desde Azure Storage con Managed Identity!" > demo.txt
az storage blob upload \
  --file demo.txt \
  --container-name "demo" \
  --name "mensaje.txt" \
  --account-name $SA \
  --auth-mode login

# 4. Verificar blob
az storage blob list --container-name "demo" --account-name $SA --auth-mode login --output table

# 5. Limpiar archivo temporal
rm demo.txt
```

### 4. Error de Despliegue

#### Síntoma

```
Deployment failed
Application failed to start
```

#### Solución

```bash
# 1. Ver logs de despliegue
az webapp log deployment list --resource-group $RG --name $APP

# 2. Ver logs en tiempo real
az webapp log tail --resource-group $RG --name $APP

# 3. Verificar estructura del ZIP
unzip -l app.zip

# Debe mostrar:
# Archive:  app.zip
#   Length      Date    Time    Name
# ---------  ---------- -----   ----
#      xxxx  xx-xx-xxxx xx:xx   app.py
#      xxxx  xx-xx-xxxx xx:xx   requirements.txt

# 4. Recrear ZIP si es necesario
cd sample-app
zip -r ../app.zip .
cd ..

# 5. Redesplegar
az webapp deployment source config-zip \
  --resource-group $RG \
  --name $APP \
  --src app.zip
```

### 5. Error de Dependencias Python

#### Síntoma

```
ModuleNotFoundError: No module named 'azure'
Package installation failed
```

#### Solución

```bash
# 1. Verificar requirements.txt
cat sample-app/requirements.txt

# 2. Verificar versión de Python configurada
az webapp config show --resource-group $RG --name $APP --query linuxFxVersion

# 3. Si es necesario, cambiar versión de Python
az webapp config set \
  --resource-group $RG \
  --name $APP \
  --linux-fx-version "PYTHON|3.10"

# 4. Verificar logs de instalación de paquetes
az webapp log tail --resource-group $RG --name $APP | grep -i "pip"
```

## 🔍 Comandos de Diagnóstico

### Verificación Completa del Estado

```bash
#!/bin/bash
# Script de diagnóstico completo

echo "=== DIAGNÓSTICO AZURE APP SERVICE MANAGED IDENTITY ==="
echo

# Variables
RG="rg-webapp-mi-lab"
APP="tu-webapp-name"
SA="tu-storage-account"

echo "1. 📊 Estado de la Web App"
az webapp show --resource-group $RG --name $APP --query '{name:name, state:state, location:location}' --output table
echo

echo "2. 🔐 Estado de Managed Identity"
az webapp identity show --resource-group $RG --name $APP --output table
echo

echo "3. 📜 Configuración de la Aplicación"
az webapp config appsettings list --resource-group $RG --name $APP --query "[?name=='AZURE_STORAGE_ACCOUNT']" --output table
echo

echo "4. 💾 Estado del Storage Account"
az storage account show --name $SA --resource-group $RG --query '{name:name, location:location, provisioningState:provisioningState}' --output table
echo

echo "5. 🔑 Asignaciones de Roles"
PRINCIPAL_ID=$(az webapp identity show -g $RG -n $APP --query principalId -o tsv 2>/dev/null)
if [ ! -z "$PRINCIPAL_ID" ]; then
    az role assignment list --assignee $PRINCIPAL_ID --output table
else
    echo "No se pudo obtener el Principal ID - Managed Identity no habilitada"
fi
echo

echo "6. 📦 Contenedores en Storage"
az storage container list --account-name $SA --auth-mode login --output table 2>/dev/null || echo "Error accediendo a Storage - verificar permisos"
echo

echo "7. 📜 Logs Recientes"
echo "Ejecuta: az webapp log tail --resource-group $RG --name $APP"
echo

echo "=== FIN DEL DIAGNÓSTICO ==="
```

### Comandos de Limpieza

```bash
# Limpiar solo la aplicación (mantener infraestructura)
az webapp restart --resource-group $RG --name $APP

# Limpiar configuración de la aplicación
az webapp config appsettings delete \
  --resource-group $RG \
  --name $APP \
  --setting-names AZURE_STORAGE_ACCOUNT

# Limpiar asignaciones de roles
PRINCIPAL_ID=$(az webapp identity show -g $RG -n $APP --query principalId -o tsv)
az role assignment delete --assignee $PRINCIPAL_ID

# Limpiar Managed Identity
az webapp identity remove --resource-group $RG --name $APP

# Limpieza completa (CUIDADO: elimina todos los recursos)
az group delete --name $RG --yes --no-wait
```

## 🚑 Contacto y Soporte

### Durante el Laboratorio

- Revisar logs: `az webapp log tail`
- Verificar estado: `az webapp show`
- Consultar documentación: [Azure App Service Docs](https://docs.microsoft.com/azure/app-service/)

### Recursos Adicionales

- [Azure CLI Reference](https://docs.microsoft.com/cli/azure/)
- [Azure SDK for Python](https://github.com/Azure/azure-sdk-for-python)
- [Managed Identity Best Practices](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/)
