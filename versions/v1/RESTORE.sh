#!/bin/bash
# Script para restaurar Versión 1
echo "Restaurando Versión 1..."
cp /app/versions/v1/backend/server.py /app/backend/
cp /app/versions/v1/frontend/src/pages/Invoices.js /app/frontend/src/pages/
cp /app/versions/v1/frontend/src/pages/Settings.js /app/frontend/src/pages/
cp /app/versions/v1/frontend/src/pages/SystemMonitor.js /app/frontend/src/pages/
echo "Restauración completada. Reinicia los servicios con:"
echo "sudo supervisorctl restart backend frontend"
