# Configuración del Laboratorio

## 🎯 Resumen Ejecutivo

Este laboratorio enseña cómo implementar **autenticación sin secrets** en Azure App Service usando **Managed Identity** y **DefaultAzureCredential**.

## 🔧 Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   Azure Portal  │────│  Azure Cloud    │────│  Azure App      │
│   (Student)     │    │  Shell (Bash)    │    │  Service        │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                          │ Managed Identity
                                                          │ (No secrets!)
                                                          ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  Azure Storage  │
                                                │  Account        │
                                                │                 │
                                                └─────────────────┘
```

## 📚 Conceptos Clave

### Managed Identity

- **¿Qué es?** Identidad automática para servicios de Azure
- **¿Por qué?** Elimina la necesidad de almacenar secrets
- **¿Cómo?** Azure maneja automáticamente la autenticación

### DefaultAzureCredential

- **Orden de autenticación:**
  1. Environment variables
  2. Managed Identity
  3. Azure CLI
  4. Visual Studio Code
  5. Azure PowerShell

## 🚀 Flujo del Laboratorio

1. **Preparación** → Variables de entorno
2. **Infraestructura** → Resource Group, App Service Plan, Web App
3. **Identidad** → Habilitar Managed Identity
4. **Storage** → Crear Storage Account y asignar permisos
5. **Código** → Aplicación Flask con Azure SDK
6. **Despliegue** → ZIP deployment
7. **Verificación** → Testing y monitoreo
8. **Limpieza** → Eliminación de recursos

## 🔍 Comandos Clave

### Managed Identity

```bash
# Habilitar
az webapp identity assign -g $RG -n $APP

# Obtener Principal ID
PRINCIPAL_ID=$(az webapp identity show -g $RG -n $APP --query principalId -o tsv)
```

### Role Assignment

```bash
# Asignar permisos mínimos necesarios
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Reader" \
  --scope $STORAGE_ID
```

### Deployment

```bash
# Despliegue con ZIP
az webapp deployment source config-zip -g $RG -n $APP --src app.zip
```

## 🛠️ Solución de Problemas

### Problema: "DefaultAzureCredential failed to retrieve a token"

**Causa:** Managed Identity no habilitada o permisos insuficientes
**Solución:**

```bash
# Verificar identidad
az webapp identity show -g $RG -n $APP

# Verificar asignaciones de rol
az role assignment list --assignee $PRINCIPAL_ID
```

### Problema: "Storage account not found"

**Causa:** Variable AZURE_STORAGE_ACCOUNT no configurada
**Solución:**

```bash
# Verificar configuración
az webapp config appsettings list -g $RG -n $APP

# Reconfigurar si es necesario
az webapp config appsettings set -g $RG -n $APP --settings AZURE_STORAGE_ACCOUNT=$SA
```

### Problema: "Application failed to start"

**Causa:** Error en requirements.txt o código
**Solución:**

```bash
# Ver logs detallados
az webapp log tail -g $RG -n $APP

# Verificar configuración de runtime
az webapp config show -g $RG -n $APP --query linuxFxVersion
```

## 📊 Métricas de Éxito

- ✅ Web App desplegada y accesible
- ✅ Managed Identity funcionando
- ✅ Acceso a Storage sin secrets
- ✅ Logs sin errores de autenticación
- ✅ Página web mostrando contenido del blob

## 🎓 Objetivos de Aprendizaje

Al completar este laboratorio, los estudiantes podrán:

1. **Explicar** qué es Managed Identity y por qué es importante
2. **Implementar** autenticación sin secrets en Azure
3. **Configurar** permisos RBAC apropiados
4. **Desplegar** aplicaciones Flask en App Service
5. **Diagnosticar** problemas comunes de autenticación
6. **Aplicar** mejores prácticas de seguridad en la nube

## 🔗 Referencias

- [Azure Managed Identity Documentation](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/)
- [Azure SDK for Python](https://github.com/Azure/azure-sdk-for-python)
- [App Service Authentication](https://docs.microsoft.com/azure/app-service/overview-authentication-authorization)
- [DefaultAzureCredential](https://docs.microsoft.com/python/api/azure-identity/azure.identity.defaultazurecredential)
