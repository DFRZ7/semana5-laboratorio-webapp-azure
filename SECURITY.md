# 🔒 Guía de Seguridad

## 🎯 Objetivo

Este documento establece las mejores prácticas de seguridad para el laboratorio y su uso en producción.

## ⚠️ Advertencias Importantes

### Para Estudiantes

- **NO uses passwords de ejemplo en producción**
- **SIEMPRE limpia los recursos** después del laboratorio
- **NO commits credentials** en repositorios
- **USA suscripciones de desarrollo/learning**, no producción

### Para Instructores

- Verificar que estudiantes usen suscripciones apropiadas
- Establecer límites de gasto en suscripciones de laboratorio
- Monitorear uso de recursos durante la sesión
- Asegurar limpieza completa al final

## 🔐 Mejores Prácticas Implementadas

### 1. Managed Identity

✅ **Implementado**: No hay secrets en el código

```python
# ✅ Correcto: Sin connection strings
credential = DefaultAzureCredential()

# ❌ Incorrecto: Hard-coded secrets
connection_string = "DefaultEndpointsProtocol=https;AccountName=..."
```

### 2. Principio de Menor Privilegio

✅ **Implementado**: Solo permisos mínimos necesarios

```bash
# Solo permisos de lectura para Storage
az role assignment create \
  --role "Storage Blob Data Reader" \
  --scope $STORAGE_ID
```

### 3. Configuración via Variables de Entorno

✅ **Implementado**: Configuración externa al código

```bash
az webapp config appsettings set \
  --settings AZURE_STORAGE_ACCOUNT=$SA
```

### 4. Limpieza de Recursos

✅ **Implementado**: Comando de limpieza incluido

```bash
az group delete --name $RG --yes --no-wait
```

## 🛡️ Para Uso en Producción

### Cambios Necesarios

1. **Passwords Seguros**

   ```bash
   # Generar password seguro
   PG_ADMIN_PASSWORD=$(openssl rand -base64 32)
   ```

2. **Nombres Úunicos y Descriptivos**

   ```bash
   # En lugar de nombres genéricos
   RG="rg-myapp-prod-eastus2"
   APP="myapp-prod-$(date +%Y%m%d)"
   ```

3. **Networking Seguro**

   ```bash
   # Restringir acceso a red
   az webapp config access-restriction add \
     --resource-group $RG \
     --name $APP \
     --rule-name "OfficeNetwork" \
     --action Allow \
     --ip-address 203.0.113.0/24
   ```

4. **Monitoreo y Alertas**

   ```bash
   # Habilitar Application Insights
   az monitor app-insights component create \
     --app $APP \
     --location $LOC \
     --resource-group $RG
   ```

5. **Backup y Disaster Recovery**
   ```bash
   # Configurar backup automático
   az webapp config backup create \
     --resource-group $RG \
     --webapp-name $APP \
     --backup-name "daily-backup"
   ```

## 🔍 Checklist de Seguridad

### Antes del Despliegue

- [ ] Passwords generados automáticamente
- [ ] Variables de entorno configuradas
- [ ] Permisos RBAC revisados
- [ ] Network security groups configurados
- [ ] SSL/TLS habilitado

### Durante el Desarrollo

- [ ] No commits de secrets
- [ ] Managed Identity funcionando
- [ ] Logs configurados apropiadamente
- [ ] Testing de seguridad realizado

### Después del Despliegue

- [ ] Monitoreo activo
- [ ] Alertas configuradas
- [ ] Backup verificado
- [ ] Documentación actualizada

## 📚 Referencias de Seguridad

- [Azure Security Best Practices](https://docs.microsoft.com/azure/security/)
- [Managed Identity Security](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
- [App Service Security](https://docs.microsoft.com/azure/app-service/overview-security)
- [Azure RBAC Best Practices](https://docs.microsoft.com/azure/role-based-access-control/best-practices)

## 🚑 Reporte de Problemas de Seguridad

Si encuentras problemas de seguridad en este laboratorio:

1. **NO** los reportes públicamente
2. Envía un email privado al instructor
3. Incluye detalles del problema y pasos para reproducir
4. Sugiere una solución si es posible

---

**Recuerda: La seguridad es responsabilidad de todos** 🔒
