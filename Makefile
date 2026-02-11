# ============================================================================
# MAKEFILE - SKIN CANCER ANALYZER
# Comandos úteis para desenvolvimento e deploy
# ============================================================================

.PHONY: help build up down restart logs shell test clean

# Cores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

# Variáveis
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := skin-cancer-analyzer

# ============================================================================
# HELP
# ============================================================================
help: ## Mostra esta mensagem de ajuda
	@echo "$(GREEN)Skin Cancer Analyzer - Docker Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# DOCKER COMPOSE
# ============================================================================
build: ## Build dos containers
	@echo "$(GREEN)Building containers...$(NC)"
	$(DOCKER_COMPOSE) build --no-cache

up: ## Inicia os containers
	@echo "$(GREEN)Starting containers...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Containers started!$(NC)"
	@echo "$(YELLOW)Access the application at: http://localhost$(NC)"

down: ## Para os containers
	@echo "$(YELLOW)Stopping containers...$(NC)"
	$(DOCKER_COMPOSE) down

restart: down up ## Reinicia os containers

stop: ## Para os containers sem remover
	@echo "$(YELLOW)Stopping containers...$(NC)"
	$(DOCKER_COMPOSE) stop

start: ## Inicia containers parados
	@echo "$(GREEN)Starting containers...$(NC)"
	$(DOCKER_COMPOSE) start

# ============================================================================
# LOGS
# ============================================================================
logs: ## Mostra logs de todos os containers
	$(DOCKER_COMPOSE) logs -f

logs-app: ## Mostra logs apenas da aplicação
	$(DOCKER_COMPOSE) logs -f app

logs-nginx: ## Mostra logs do nginx
	$(DOCKER_COMPOSE) logs -f nginx

logs-db: ## Mostra logs do banco de dados
	$(DOCKER_COMPOSE) logs -f postgres

# ============================================================================
# SHELL ACCESS
# ============================================================================
shell: ## Acessa shell do container da aplicação
	$(DOCKER_COMPOSE) exec app /bin/bash

shell-nginx: ## Acessa shell do nginx
	$(DOCKER_COMPOSE) exec nginx /bin/sh

shell-db: ## Acessa shell do PostgreSQL
	$(DOCKER_COMPOSE) exec postgres psql -U skin_cancer_user -d skin_cancer

# ============================================================================
# DATABASE
# ============================================================================
db-init: ## Inicializa o banco de dados
	@echo "$(GREEN)Initializing database...$(NC)"
	$(DOCKER_COMPOSE) exec app python -c "from app import db; db.create_all()"

db-migrate: ## Executa migrations
	@echo "$(GREEN)Running migrations...$(NC)"
	$(DOCKER_COMPOSE) exec app flask db upgrade

db-backup: ## Backup do banco de dados
	@echo "$(GREEN)Creating database backup...$(NC)"
	$(DOCKER_COMPOSE) exec postgres pg_dump -U skin_cancer_user skin_cancer > backup_$$(date +%Y%m%d_%H%M%S).sql

db-restore: ## Restaura backup do banco (usar: make db-restore FILE=backup.sql)
	@echo "$(YELLOW)Restoring database from $(FILE)...$(NC)"
	$(DOCKER_COMPOSE) exec -T postgres psql -U skin_cancer_user -d skin_cancer < $(FILE)

# ============================================================================
# DEVELOPMENT
# ============================================================================
dev: ## Inicia em modo desenvolvimento
	@echo "$(GREEN)Starting in development mode...$(NC)"
	FLASK_ENV=development $(DOCKER_COMPOSE) up

watch: ## Inicia com hot-reload
	@echo "$(GREEN)Starting with hot-reload...$(NC)"
	$(DOCKER_COMPOSE) up --build

# ============================================================================
# TESTING
# ============================================================================
test: ## Executa testes
	@echo "$(GREEN)Running tests...$(NC)"
	$(DOCKER_COMPOSE) exec app pytest

test-coverage: ## Executa testes com coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(DOCKER_COMPOSE) exec app pytest --cov=app --cov-report=html

# ============================================================================
# MONITORING
# ============================================================================
monitoring-up: ## Inicia serviços de monitoramento (Prometheus + Grafana)
	@echo "$(GREEN)Starting monitoring services...$(NC)"
	$(DOCKER_COMPOSE) --profile monitoring up -d
	@echo "$(YELLOW)Prometheus: http://localhost:9090$(NC)"
	@echo "$(YELLOW)Grafana: http://localhost:3000 (admin/admin)$(NC)"

admin-up: ## Inicia PgAdmin
	@echo "$(GREEN)Starting PgAdmin...$(NC)"
	$(DOCKER_COMPOSE) --profile admin up -d
	@echo "$(YELLOW)PgAdmin: http://localhost:5050$(NC)"

# ============================================================================
# MAINTENANCE
# ============================================================================
ps: ## Lista containers em execução
	$(DOCKER_COMPOSE) ps

stats: ## Mostra estatísticas dos containers
	docker stats $$(docker ps --filter name=$(PROJECT_NAME) --format "{{.Names}}")

prune: ## Remove containers, volumes e imagens não utilizados
	@echo "$(RED)WARNING: This will remove all unused Docker resources!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker system prune -a --volumes; \
	fi

clean: down ## Para e remove containers, volumes e redes
	@echo "$(YELLOW)Cleaning up...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

rebuild: clean build up ## Rebuild completo do zero

# ============================================================================
# PRODUCTION
# ============================================================================
prod-deploy: ## Deploy em produção
	@echo "$(GREEN)Deploying to production...$(NC)"
	@echo "$(YELLOW)⚠️  Make sure you have configured SSL certificates and .env file!$(NC)"
	FLASK_ENV=production $(DOCKER_COMPOSE) up -d --build
	@echo "$(GREEN)✓ Production deployment complete!$(NC)"

prod-logs: ## Logs de produção
	$(DOCKER_COMPOSE) logs -f --tail=100

# ============================================================================
# SECURITY
# ============================================================================
scan: ## Scan de vulnerabilidades nas imagens
	@echo "$(GREEN)Scanning for vulnerabilities...$(NC)"
	docker scan $(PROJECT_NAME)_app:latest

update: ## Atualiza todas as dependências
	@echo "$(GREEN)Updating dependencies...$(NC)"
	$(DOCKER_COMPOSE) exec app pip install --upgrade pip
	$(DOCKER_COMPOSE) exec app pip list --outdated

# ============================================================================
# BACKUP
# ============================================================================
backup: ## Backup completo (banco + uploads)
	@echo "$(GREEN)Creating full backup...$(NC)"
	mkdir -p backups
	$(DOCKER_COMPOSE) exec postgres pg_dump -U skin_cancer_user skin_cancer > backups/db_$$(date +%Y%m%d_%H%M%S).sql
	tar -czf backups/uploads_$$(date +%Y%m%d_%H%M%S).tar.gz uploads/
	@echo "$(GREEN)✓ Backup complete!$(NC)"

# ============================================================================
# INFO
# ============================================================================
version: ## Mostra versões dos componentes
	@echo "$(GREEN)Component Versions:$(NC)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"
	@echo "Python: $$($(DOCKER_COMPOSE) exec app python --version 2>&1 || echo 'N/A')"

health: ## Verifica saúde dos serviços
	@echo "$(GREEN)Checking service health...$(NC)"
	@curl -f http://localhost/health && echo "$(GREEN)✓ Application: Healthy$(NC)" || echo "$(RED)✗ Application: Unhealthy$(NC)"

.DEFAULT_GOAL := help
