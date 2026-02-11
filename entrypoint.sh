#!/bin/bash
# ============================================================================
# ENTRYPOINT.SH - SKIN CANCER ANALYZER
# Script de inicialização do container
# ============================================================================

set -e

echo "=================================================="
echo "  SKIN CANCER ANALYZER - Initializing..."
echo "=================================================="

# ============================================================================
# VARIÁVEIS DE AMBIENTE
# ============================================================================
export PYTHONUNBUFFERED=1
export FLASK_APP=${FLASK_APP:-app.py}
export FLASK_ENV=${FLASK_ENV:-production}

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_tries=30
    local count=0

    echo "⏳ Waiting for $service_name at $host:$port..."
    
    while ! nc -z "$host" "$port" > /dev/null 2>&1; do
        count=$((count + 1))
        if [ $count -gt $max_tries ]; then
            echo "❌ ERROR: $service_name not available after $max_tries attempts"
            exit 1
        fi
        echo "   Attempt $count/$max_tries..."
        sleep 2
    done
    
    echo "✅ $service_name is ready!"
}

# ============================================================================
# AGUARDAR SERVIÇOS DEPENDENTES
# ============================================================================
if [ ! -z "$DATABASE_URL" ]; then
    # Extrair host e porta do DATABASE_URL se necessário
    if [[ $DATABASE_URL == *"postgres"* ]]; then
        wait_for_service "postgres" 5432 "PostgreSQL"
    fi
fi

if [ ! -z "$REDIS_URL" ] || [ ! -z "$REDIS_HOST" ]; then
    REDIS_HOST=${REDIS_HOST:-redis}
    REDIS_PORT=${REDIS_PORT:-6379}
    wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
fi

# ============================================================================
# CRIAR DIRETÓRIOS NECESSÁRIOS
# ============================================================================
echo "📁 Creating required directories..."
mkdir -p ${UPLOAD_FOLDER:-/app/uploads}
mkdir -p ${MODEL_PATH:-/app/models}
mkdir -p /app/logs
mkdir -p /app/static

# ============================================================================
# VERIFICAR MODELO DE IA
# ============================================================================
MODEL_FILE="${MODEL_PATH:-/app/models}/skin_cancer_model.h5"
if [ ! -f "$MODEL_FILE" ]; then
    echo "⚠️  WARNING: AI model not found at $MODEL_FILE"
    echo "   Please ensure the model is mounted or copied to the container"
    echo "   The application may fail to start without a valid model"
fi

# ============================================================================
# INICIALIZAR BANCO DE DADOS (se necessário)
# ============================================================================
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🔄 Running database migrations..."
    python -c "from app import db; db.create_all()" || echo "⚠️  Migration failed or not applicable"
fi

# ============================================================================
# HEALTH CHECK INTERNO
# ============================================================================
echo "🏥 Running internal health check..."
python -c "
import sys
try:
    import flask
    import numpy
    import PIL
    # import tensorflow as tf  # Descomente se usar TensorFlow
    print('✅ All critical dependencies loaded successfully')
    sys.exit(0)
except ImportError as e:
    print(f'❌ ERROR: Missing critical dependency: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Health check failed - exiting"
    exit 1
fi

# ============================================================================
# LOG DE CONFIGURAÇÃO
# ============================================================================
echo "=================================================="
echo "  Configuration:"
echo "  - FLASK_ENV: $FLASK_ENV"
echo "  - FLASK_APP: $FLASK_APP"
echo "  - MODEL_PATH: ${MODEL_PATH:-/app/models}"
echo "  - UPLOAD_FOLDER: ${UPLOAD_FOLDER:-/app/uploads}"
echo "  - LOG_LEVEL: ${LOG_LEVEL:-INFO}"
echo "=================================================="

# ============================================================================
# EXECUTAR COMANDO
# ============================================================================
echo "🚀 Starting application..."
echo "=================================================="

# Se nenhum comando foi passado, usar o CMD padrão do Dockerfile
if [ $# -eq 0 ]; then
    echo "ℹ️  No command provided, using default CMD from Dockerfile"
    exit 0
fi

# Executar o comando passado como argumento
echo "▶️  Executing: $@"
exec "$@"
