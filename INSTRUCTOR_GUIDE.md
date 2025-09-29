# 🎓 Guía para el Instructor

## 📋 Resumen del Laboratorio

Este laboratorio enseña a los estudiantes cómo desplegar una aplicación Flask en Azure App Service usando **Managed Identity** para autenticación segura sin secrets.

### ⏱️ Tiempo Estimado

- **Duración total**: 45-60 minutos
- **Preparación**: 5 minutos
- **Ejecución**: 35-45 minutos
- **Discusión**: 10 minutos

### 👥 Audiencia

- Estudiantes con conocimiento básico de Azure
- Experiencia básica con línea de comandos
- Conceptos fundamentales de desarrollo web

## 🎯 Objetivos de Aprendizaje

Al finalizar este laboratorio, los estudiantes podrán:

1. **Explicar** qué es Managed Identity y sus beneficios
2. **Implementar** autenticación sin secrets en Azure
3. **Configurar** RBAC apropiadamente
4. **Desplegar** aplicaciones Flask en App Service
5. **Diagnosticar** problemas comunes de autenticación

## 📚 Conceptos Clave a Enfatizar

### 1. Managed Identity

- **Sin secrets**: No hay connection strings en el código
- **Automático**: Azure maneja la rotación de tokens
- **Seguro**: Reduce la superficie de ataque

### 2. DefaultAzureCredential

- **Cadena de autenticación**: Multiple métodos de respaldo
- **Desarrollo vs Producción**: Funciona en ambos entornos
- **Best practice**: Patrón recomendado por Microsoft

### 3. Principio de Menor Privilegio

- **Permisos mínimos**: Solo "Storage Blob Data Reader"
- **Scope específico**: Solo al Storage Account necesario
- **Auditoría**: Roles asignados son rastreables

## 🚀 Flujo de la Clase

### Fase 1: Introducción (5 minutos)

```
📌 Puntos a cubrir:
- ¿Por qué Managed Identity?
- Problemas con connection strings
- Demostración del resultado final
```

### Fase 2: Configuración (10 minutos)

```
📌 Comandos críticos:
- az login y selección de suscripción
- Definición de variables
- Creación de Resource Group
```

### Fase 3: Infraestructura (15 minutos)

```
📌 Recursos a crear:
- App Service Plan
- Web App
- Storage Account
- Managed Identity
```

### Fase 4: Seguridad (10 minutos)

```
📌 Configuración RBAC:
- Asignación de roles
- Verificación de permisos
- Variables de aplicación
```

### Fase 5: Despliegue (10 minutos)

```
📌 Deployment:
- ZIP deployment
- Monitoreo de logs
- Verificación funcional
```

### Fase 6: Validación (5 minutos)

```
📌 Testing:
- Acceso a la aplicación
- Pruebas de funcionalidad
- Revisión de logs
```

## 🔍 Puntos de Verificación

### Checkpoint 1: Infraestructura Base

```bash
# Verificar que todos los recursos existen
az group show --name $RG
az appservice plan show --name $PLAN --resource-group $RG
az webapp show --name $APP --resource-group $RG
```

### Checkpoint 2: Managed Identity

```bash
# Verificar identidad asignada
az webapp identity show --resource-group $RG --name $APP
```

### Checkpoint 3: Permisos

```bash
# Verificar role assignment
PRINCIPAL_ID=$(az webapp identity show -g $RG -n $APP --query principalId -o tsv)
az role assignment list --assignee $PRINCIPAL_ID
```

### Checkpoint 4: Aplicación

```bash
# Verificar deployment
az webapp browse --resource-group $RG --name $APP
```

## 🚨 Problemas Comunes y Soluciones

### Problema: Estudiante no puede crear recursos

**Causa**: Permisos insuficientes en la suscripción
**Solución**: Verificar rol "Contributor" en la suscripción

### Problema: Managed Identity no funciona

**Causa**: Role assignment no aplicado correctamente
**Solución**: Esperar 2-3 minutos para propagación de permisos

### Problema: Aplicación no inicia

**Causa**: Error en requirements.txt o código
**Solución**: Revisar logs con `az webapp log tail`

### Problema: Storage no accesible

**Causa**: Contenedor o blob no existe
**Solución**: Verificar y recrear contenedor/blob

## 🎪 Demostraciones

### Demo 1: Problema con Connection Strings

```python
# ❌ Malo: Hard-coded connection string
connection_string = "DefaultEndpointsProtocol=https;AccountName=..."

# ✅ Bueno: Managed Identity
credential = DefaultAzureCredential()
```

### Demo 2: Logs en Tiempo Real

```bash
# Mostrar logs mientras la aplicación arranca
az webapp log tail --resource-group $RG --name $APP
```

### Demo 3: Seguridad

```bash
# Mostrar que no hay secrets en la configuración
az webapp config appsettings list --resource-group $RG --name $APP
```

## 📊 Métricas de Éxito

### Para el Instructor

- [ ] Todos los estudiantes completan el laboratorio
- [ ] Aplicaciones funcionando correctamente
- [ ] Estudiantes entienden conceptos de Managed Identity
- [ ] Preguntas respondidas satisfactoriamente

### Para los Estudiantes

- [ ] Web App desplegada y accesible
- [ ] Managed Identity habilitada
- [ ] Acceso a Storage funcionando
- [ ] Comprensión de los beneficios de seguridad

## 🎯 Preguntas de Evaluación

### Preguntas Conceptuales

1. ¿Cuál es la diferencia entre System-assigned y User-assigned Managed Identity?
2. ¿Por qué es importante el principio de menor privilegio?
3. ¿Qué sucede si rotas las credenciales en Managed Identity?

### Preguntas Prácticas

1. ¿Cómo verificarías que Managed Identity está funcionando?
2. ¿Qué comando usarías para ver los logs de la aplicación?
3. ¿Cómo añadirías permisos adicionales a la identidad?

## 🔧 Configuración Previa del Laboratorio

### Requisitos del Instructor

```bash
# Verificar Azure CLI
az --version

# Verificar permisos en suscripción
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv)

# Verificar cuotas disponibles
az vm list-usage --location canadacentral
```

### Preparación del Entorno

```bash
# Crear suscripción de laboratorio si es necesario
# Configurar límites de gasto
# Preparar cuentas de estudiantes
```

## 📚 Recursos Adicionales para Estudiantes

### Durante el Laboratorio

- [Azure CLI Reference](https://docs.microsoft.com/cli/azure/)
- [App Service Documentation](https://docs.microsoft.com/azure/app-service/)

### Después del Laboratorio

- [Managed Identity Deep Dive](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/)
- [Azure Security Best Practices](https://docs.microsoft.com/azure/security/)

## 🎉 Actividades de Extensión

### Para Estudiantes Avanzados

1. Implementar la versión con PostgreSQL
2. Agregar Application Insights para monitoreo
3. Configurar múltiples entornos (dev/staging/prod)
4. Implementar CI/CD con GitHub Actions

### Proyectos de Seguimiento

1. Migrar una aplicación existente a Managed Identity
2. Implementar Key Vault para secrets adicionales
3. Configurar networking con VNet integration

## 📝 Notas del Instructor

### Timing Suggestions

- No acelerar la sección de RBAC - es crítica
- Permitir tiempo extra para troubleshooting
- Usar demos en vivo en lugar de screenshots

### Engagement Tips

- Hacer preguntas durante la demo
- Pedir a estudiantes que expliquen cada paso
- Comparar con métodos tradicionales

### Assessment Ideas

- Lab completion checklist
- Quick quiz sobre conceptos
- Peer review de configuraciones

---

**¡Que tengas una excelente sesión de laboratorio!** 🚀
