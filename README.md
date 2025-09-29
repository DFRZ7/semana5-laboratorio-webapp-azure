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

Abre Azure Cloud Shell desde el portal de Azure y ejecuta:

```bash
# Configurar suscripción
az account set --subscription "<TU_SUBSCRIPTION_ID>"

# Verificar suscripción activa
az account show --query name -o tsv
```

### 2. Definir Variables de Entorno

```bash
# Variables del laboratorio
RG="rg-webapp-mi-lab"
LOC="canadacentral"
PLAN="plan-webapp-mi-lab"
APP="webapp-mi-lab-$RANDOM"
SA="st${RANDOM}milab"

# Mostrar variables para verificar
echo "Resource Group: $RG"
echo "Location: $LOC"
echo "App Service Plan: $PLAN"
echo "Web App: $APP"
echo "Storage Account: $SA"
```

### 3. Crear Recursos Base

```bash
# Crear grupo de recursos
az group create --name $RG --location $LOC

# Crear App Service Plan (Linux, B1)
az appservice plan create \
  --name $PLAN \
  --resource-group $RG \
  --sku B1 \
  --is-linux

# Crear Web App con Python 3.10
az webapp create \
  --name $APP \
  --resource-group $RG \
  --plan $PLAN \
  --runtime "PYTHON:3.10"
```

### 4. Habilitar Managed Identity

```bash
# Asignar identidad administrada a la Web App
az webapp identity assign \
  --resource-group $RG \
  --name $APP

# Obtener el Principal ID de la identidad
PRINCIPAL_ID=$(az webapp identity show \
  --resource-group $RG \
  --name $APP \
  --query principalId \
  --output tsv)

echo "Principal ID: $PRINCIPAL_ID"
```

### 5. Crear Azure Storage Account

```bash
# Crear Storage Account
az storage account create \
  --name $SA \
  --resource-group $RG \
  --location $LOC \
  --sku Standard_LRS

# Obtener el ID del Storage Account
STORAGE_ID=$(az storage account show \
  --name $SA \
  --resource-group $RG \
  --query id \
  --output tsv)

# Asignar rol de Storage Blob Data Reader
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Reader" \
  --scope $STORAGE_ID
```

### 6. Crear Contenedor y Blob de Prueba

```bash
# Crear contenedor
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

```bash
# Configurar el nombre del Storage Account en la Web App
az webapp config appsettings set \
  --resource-group $RG \
  --name $APP \
  --settings AZURE_STORAGE_ACCOUNT=$SA
```

### 8. Descargar y Preparar el Código

```bash
# Clonar el repositorio del laboratorio
git clone https://github.com/DFRZ7/semana5-laboratorio-webapp-azure.git
cd semana5-laboratorio-webapp-azure/sample-app
```

### 9. Desplegar la Aplicación

```bash
# Crear archivo ZIP con la aplicación
zip -r ../app.zip .
cd ..

# Desplegar usando Azure CLI
az webapp deployment source config-zip \
  --resource-group $RG \
  --name $APP \
  --src app.zip
```

### 10. Verificar el Despliegue

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

### 11. Monitorear la Aplicación

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

### 12. Limpieza de Recursos

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
