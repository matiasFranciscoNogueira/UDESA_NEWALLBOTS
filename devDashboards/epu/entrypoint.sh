#!/bin/bash
set -e

# ──────────────────────────────────────────────
# Cron: reimportar Excel el día 6 de cada mes a las 12:00
# (24 hs después de que el bot EPU genera el Excel nuevo)
# ──────────────────────────────────────────────
(crontab -l 2>/dev/null; echo "0 12 6 * * cd /app && python scripts/import_excel_to_sqlite.py >> /var/log/import_cron.log 2>&1") | crontab -

# ──────────────────────────────────────────────
# Importar Excel al deployar
# Si el Excel no existe todavía (primer deploy, bot EPU aún corriendo),
# el dashboard arranca sin datos y se actualiza en el próximo cron mensual.
# ──────────────────────────────────────────────
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Importando Excel a SQLite..."
cd /app && python scripts/import_excel_to_sqlite.py \
    || echo "[$(date '+%Y-%m-%d %H:%M:%S')] AVISO: Excel no encontrado. El dashboard arranca sin datos — se importará automáticamente el día 6 de cada mes."

# ──────────────────────────────────────────────
# Watcher: re-importar cuando el bot EPU actualice el Excel
# Consulta cada 60 s; si el mtime cambió, reimporta a SQLite.
# ──────────────────────────────────────────────
EXCEL_PATH="/app/data/all_subcategories_compare.xlsx"
(
    LAST_MTIME=$(stat -c %Y "$EXCEL_PATH" 2>/dev/null || echo "0")
    while true; do
        sleep 60
        CURRENT_MTIME=$(stat -c %Y "$EXCEL_PATH" 2>/dev/null || echo "0")
        if [ "$CURRENT_MTIME" != "0" ] && [ "$CURRENT_MTIME" != "$LAST_MTIME" ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Excel actualizado — reimportando a SQLite..."
            cd /app && python scripts/import_excel_to_sqlite.py >> /var/log/import_cron.log 2>&1
            LAST_MTIME="$CURRENT_MTIME"
        fi
    done
) &

# ──────────────────────────────────────────────
# Iniciar cron en background y dashboard en primer plano
# ──────────────────────────────────────────────
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cron activo — próxima importación: día 6 del mes a las 12:00"
cron

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando dashboard en http://0.0.0.0:8050 ..."
exec python src/main.py
