# ============================================================================
# DOCKERFILE - SKIN CANCER ANALYZER
# Multi-stage build para otimização de tamanho e segurança
# ============================================================================

# ============================================================================
# STAGE 1: BUILDER - Compilação e instalação de dependências
# ============================================================================
FROM python:3.11-slim as builder

LABEL maintainer="VerticalAgent <contato@verticalagent.com.br>"
LABEL description="Skin Cancer Analyzer - AI-powered skin lesion analysis"
LABEL version="1.0"

# Argumentos de build
ARG APP_ENV=production
ARG DEBIAN_FRONTEND=noninteractive

# Variáveis de ambiente para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1

# Instalar dependências do sistema necessárias para compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /build

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências Python em diretório isolado
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefix=/install --no-warn-script-location -r requirements.txt

# ============================================================================
# STAGE 2: RUNTIME - Imagem final otimizada
# ============================================================================
FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH" \
    APP_HOME=/app \
    MODEL_PATH=/app/models \
    UPLOAD_FOLDER=/app/uploads \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Argumentos de build
ARG APP_USER=appuser
ARG APP_UID=1000
ARG APP_GID=1000

# Instalar dependências runtime mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuário não-root para segurança
RUN groupadd -g ${APP_GID} ${APP_USER} && \
    useradd -m -u ${APP_UID} -g ${APP_GID} -s /bin/bash ${APP_USER}

# Criar diretórios necessários
RUN mkdir -p ${APP_HOME} ${MODEL_PATH} ${UPLOAD_FOLDER} && \
    chown -R ${APP_USER}:${APP_USER} ${APP_HOME} ${MODEL_PATH} ${UPLOAD_FOLDER}

# Copiar dependências instaladas do builder
COPY --from=builder /install /usr/local

# Mudar para diretório da aplicação
WORKDIR ${APP_HOME}

# Copiar código da aplicação
COPY --chown=${APP_USER}:${APP_USER} . .

# Copiar script de entrypoint
COPY --chown=${APP_USER}:${APP_USER} entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Criar diretórios para logs
RUN mkdir -p /app/logs && chown -R ${APP_USER}:${APP_USER} /app/logs

# Mudar para usuário não-root
USER ${APP_USER}

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expor porta da aplicação
EXPOSE 5000

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Comando padrão (pode ser sobrescrito)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
