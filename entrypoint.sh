#!/bin/bash
set -e

# Define porta dinâmica baseada na variável PORT do Cloud Run
export APP_PORT=${PORT:-5000}

echo "Iniciando aplicação na porta ${APP_PORT}..."

# Garante permissões nos diretórios
mkdir -p /app/logs /app/uploads /app/models
chown -R ${APP_USER:-appuser}:${APP_USER:-appuser} /app/logs /app/uploads /app/models 2>/dev/null || true

# Inicia o Gunicorn com porta dinâmica
exec gunicorn \
  --bind "0.0.0.0:${APP_PORT}" \
  --workers ${WEB_CONCURRENCY:-4} \
  --threads ${WEB_THREADS:-2} \
  --timeout ${WEB_TIMEOUT:-120} \
  --keep-alive 5 \
  --access-logfile "-" \
  --error-logfile "-" \
  --log-level info \
  "app:app"
