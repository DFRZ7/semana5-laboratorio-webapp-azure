# 🐘 Configuración con PostgreSQL Flexible Server

## 🎯 Opción Alternativa: PostgreSQL + Managed Identity

Esta guía muestra cómo usar PostgreSQL Flexible Server en lugar de Azure Storage.

## 🚀 Comandos Adicionales para PostgreSQL

### 1. Variables Adicionales

```bash
# Variables para PostgreSQL (agregar después de las variables existentes)
PG_SERVER="pgmi${RANDOM}"
PG_DATABASE="demodb"
PG_ADMIN_USER="pgadmin"
PG_ADMIN_PASSWORD="TuPasswordSeguro123!"  # CAMBIAR por password seguro
PG_MI_USER="webapp_mi_user"

echo "PostgreSQL Server: $PG_SERVER"
echo "Database: $PG_DATABASE"
echo "MI User: $PG_MI_USER"
```

### 2. Crear PostgreSQL Flexible Server

```bash
# Crear PostgreSQL Flexible Server
az postgres flexible-server create \
  --name $PG_SERVER \
  --resource-group $RG \
  --location $LOC \
  --admin-user $PG_ADMIN_USER \
  --admin-password $PG_ADMIN_PASSWORD \
  --tier Burstable \
  --sku-name B1ms \
  --storage-size 32 \
  --version 14

# Configurar firewall (permitir servicios de Azure)
az postgres flexible-server firewall-rule create \
  --resource-group $RG \
  --name $PG_SERVER \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 3. Configurar Azure AD Authentication

```bash
# Habilitar autenticación Azure AD
az postgres flexible-server ad-admin create \
  --resource-group $RG \
  --server-name $PG_SERVER \
  --display-name "Azure AD Admin" \
  --object-id $(az ad signed-in-user show --query id -o tsv)

# Crear base de datos
az postgres flexible-server db create \
  --resource-group $RG \
  --server-name $PG_SERVER \
  --database-name $PG_DATABASE
```

### 4. Crear Usuario para Managed Identity

```bash
# Conectarse como administrador y crear usuario MI
# Nota: Esto requiere psql instalado localmente o usar Cloud Shell

# Obtener connection string
PG_CONNECTION_STRING=$(az postgres flexible-server show-connection-string \
  --server-name $PG_SERVER \
  --database-name $PG_DATABASE \
  --admin-user $PG_ADMIN_USER \
  --admin-password $PG_ADMIN_PASSWORD)

echo "Connection string: $PG_CONNECTION_STRING"

# Comando SQL para crear usuario (ejecutar manualmente en psql)
cat << EOF
CONECTAR A POSTGRESQL Y EJECUTAR:

-- Crear usuario para Managed Identity
CREATE ROLE "$PG_MI_USER" WITH LOGIN;

-- Otorgar permisos
GRANT CONNECT ON DATABASE "$PG_DATABASE" TO "$PG_MI_USER";
GRANT USAGE ON SCHEMA public TO "$PG_MI_USER";
GRANT CREATE ON SCHEMA public TO "$PG_MI_USER";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "$PG_MI_USER";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "$PG_MI_USER";

EOF
```

### 5. Configurar App Service para PostgreSQL

```bash
# Configurar variables de entorno para PostgreSQL
az webapp config appsettings set \
  --resource-group $RG \
  --name $APP \
  --settings \
    AZURE_POSTGRESQL_SERVER=$PG_SERVER \
    AZURE_POSTGRESQL_DATABASE=$PG_DATABASE \
    AZURE_POSTGRESQL_USER=$PG_MI_USER
```

### 6. Modificar requirements.txt para PostgreSQL

```bash
# Actualizar requirements.txt para incluir psycopg2
cat > sample-app/requirements.txt << EOF
# Flask Web Framework
Flask==3.0.0

# Azure Identity for Managed Identity authentication
azure-identity==1.15.0

# PostgreSQL adapter
psycopg2-binary==2.9.7

# Production WSGI server
gunicorn==21.2.0
EOF
```

### 7. Usar app_postgresql.py

```bash
# Reemplazar app.py con la versión de PostgreSQL
cp sample-app/app_postgresql.py sample-app/app.py

# Redesplegar
cd sample-app
zip -r ../app.zip .
cd ..

az webapp deployment source config-zip \
  --resource-group $RG \
  --name $APP \
  --src app.zip
```

## 🔧 Troubleshooting PostgreSQL

### Error: "password authentication failed"

```bash
# Verificar configuración Azure AD
az postgres flexible-server ad-admin list \
  --resource-group $RG \
  --server-name $PG_SERVER

# Verificar que el usuario MI existe
# Conectar como admin y ejecutar:
# SELECT rolname FROM pg_roles WHERE rolname = 'webapp_mi_user';
```

### Error: "connection refused"

```bash
# Verificar reglas de firewall
az postgres flexible-server firewall-rule list \
  --resource-group $RG \
  --name $PG_SERVER \
  --output table

# Verificar estado del servidor
az postgres flexible-server show \
  --resource-group $RG \
  --name $PG_SERVER \
  --query '{name:name, state:state, version:version}'
```

### Error: "permission denied"

```bash
# Verificar permisos del usuario MI
# Conectar como admin y ejecutar:
# \du webapp_mi_user
# \l+ demodb
```

## 📊 Ventajas de PostgreSQL vs Storage

| Aspecto           | Azure Storage                       | PostgreSQL                        |
| ----------------- | ----------------------------------- | --------------------------------- |
| **Casos de uso**  | Archivos, blobs, contenido estático | Datos relacionales, transacciones |
| **Complejidad**   | Simple                              | Moderada                          |
| **Costo**         | Muy bajo                            | Moderado                          |
| **Escalabilidad** | Muy alta                            | Alta                              |
| **Consultas**     | Limitadas                           | SQL completo                      |
| **ACID**          | No                                  | Sí                                |

## 🔗 Referencias

- [Azure Database for PostgreSQL Flexible Server](https://docs.microsoft.com/azure/postgresql/flexible-server/)
- [Azure AD Authentication with PostgreSQL](https://docs.microsoft.com/azure/postgresql/flexible-server/how-to-configure-sign-in-azure-ad-authentication)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
