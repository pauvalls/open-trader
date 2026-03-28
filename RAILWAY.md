# ============================================
# Open Trader - Railway Deployment Guide
# ============================================

## Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-url)

### Manual Deploy

1. **Fork este repo** a tu cuenta de GitHub

2. **Crear proyecto en Railway:**
   ```bash
   railway login
   railway init
   ```

3. **Añadir variables de entorno** en Railway Dashboard:
   - `SECRET_KEY` - Genera con: `openssl rand -hex 32`
   - `TELEGRAM_BOT_TOKEN` - Opcional
   - `TELEGRAM_CHAT_ID` - Opcional
   - `DISCORD_WEBHOOK_URL` - Opcional

4. **Deploy:**
   ```bash
   railway up
   ```

5. **Obtener URL:**
   ```bash
   railway domain
   ```

## Variables Requeridas

| Variable | Descripción | Generación |
|----------|-------------|------------|
| `SECRET_KEY` | Clave para firmar tokens | `openssl rand -hex 32` |

## Variables Opcionales (Alertas)

| Variable | Descripción | Dónde obtener |
|----------|-------------|---------------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | @BotFather |
| `TELEGRAM_CHAT_ID` | ID del chat para alertas | API de Telegram |
| `DISCORD_WEBHOOK_URL` | URL del webhook de Discord | Server Settings → Webhooks |

## Troubleshooting

### Error: "No module named 'xxx'"
- Asegúrate de que `requirements.txt` está actualizado
- Railway hace build automático en cada push

### Error: "Permission denied"
- El Dockerfile usa usuario no-root (`trader`)
- Asegúrate de que los archivos tienen permisos correctos

### Base de datos SQLite en Railway
- Railway tiene filesystem efímero
- Para datos persistentes, usar Railway Volumes o migrar a PostgreSQL
- El sistema creará la DB automáticamente en `./data/`

## Escala

Para escalar workers en Railway:

```bash
railway variables set WORKERS=4
```

Y modificar el startCommand en `railway.toml`.

## Monitoreo

- Railway Dashboard muestra logs en tiempo real
- Health check en `/health/`
- Métricas de uso de recursos disponibles en dashboard
