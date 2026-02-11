# 🐳 SKIN CANCER ANALYZER - DOCKER SETUP

Documentação completa para deployment com Docker.

## 📋 Índice

- [Pré-requisitos](#pré-requisitos)
- [Instalação Rápida](#instalação-rápida)
- [Configuração](#configuração)
- [Uso](#uso)
- [Arquitetura](#arquitetura)
- [Comandos Úteis](#comandos-úteis)
- [Produção](#produção)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Pré-requisitos

- **Docker** >= 20.10.0
- **Docker Compose** >= 2.0.0
- **Git**
- Mínimo 4GB RAM disponível
- 10GB de espaço em disco

### Verificar Instalação

```bash
docker --version
docker-compose --version
```

---

## 🚀 Instalação Rápida

### 1. Clone o Repositório

```bash
git clone https://github.com/amos-fernandes/Skin-cancer-Analyzer.git
cd Skin-cancer-Analyzer
```

### 2. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure:
- `SECRET_KEY` (use uma chave aleatória segura)
- `POSTGRES_PASSWORD` (senha do banco de dados)
- Outras variáveis conforme necessário

### 3. Criar Diretórios Necessários

```bash
mkdir -p models uploads logs static ssl
```

### 4. Adicionar Modelo de IA

Coloque seu modelo treinado em:
```bash
cp seu_modelo.h5 models/skin_cancer_model.h5
```

### 5. Build e Start

```bash
# Usando Make (recomendado)
make build
make up

# OU usando Docker Compose direto
docker-compose build
docker-compose up -d
```

### 6. Verificar Status

```bash
make health
# OU
curl http://localhost/health
```

### 7. Acessar Aplicação

Abra no navegador: **http://localhost**

---

## ⚙️ Configuração

### Estrutura de Arquivos

```
Skin-cancer-Analyzer/
├── Dockerfile              # Configuração da imagem Docker
├── docker-compose.yml      # Orquestração de serviços
├── nginx.conf              # Configuração do Nginx
├── entrypoint.sh           # Script de inicialização
├── requirements.txt        # Dependências Python
├── .dockerignore          # Arquivos excluídos do build
├── .env                   # Variáveis de ambiente (criar a partir de .env.example)
├── .env.example           # Template de variáveis de ambiente
├── Makefile               # Comandos úteis
├── app.py                 # Aplicação principal
├── models/                # Modelos de IA
│   └── skin_cancer_model.h5
├── uploads/               # Uploads de usuários
├── logs/                  # Logs da aplicação
├── static/                # Arquivos estáticos
└── ssl/                   # Certificados SSL (produção)
```

### Variáveis de Ambiente Importantes

| Variável | Descrição | Valor Padrão |
|----------|-----------|--------------|
| `FLASK_ENV` | Ambiente da aplicação | `production` |
| `SECRET_KEY` | Chave secreta do Flask | (deve ser alterado) |
| `DATABASE_URL` | URL do PostgreSQL | `postgresql://...` |
| `MODEL_PATH` | Caminho do modelo de IA | `/app/models` |
| `UPLOAD_FOLDER` | Pasta de uploads | `/app/uploads` |
| `MAX_CONTENT_LENGTH` | Tamanho máximo de upload | `16777216` (16MB) |

---

## 🏗️ Arquitetura

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ HTTP/HTTPS
       │
┌──────▼──────────────────────────────────┐
│           NGINX (Port 80/443)           │
│   - Reverse Proxy                       │
│   - SSL Termination                     │
│   - Static Files                        │
│   - Rate Limiting                       │
└──────┬──────────────────────────────────┘
       │
       │ Proxy to Backend
       │
┌──────▼──────────────────────────────────┐
│      Flask App (Gunicorn) :5000         │
│   - REST API                            │
│   - AI Model Inference                  │
│   - Business Logic                      │
└──┬────┬────┬────────────────────────────┘
   │    │    │
   │    │    └─────────┐
   │    │              │
   │    ▼              ▼
   │  ┌────────┐   ┌────────┐
   │  │ Redis  │   │Postgres│
   │  │ :6379  │   │ :5432  │
   │  └────────┘   └────────┘
   │
   └──► Filesystem
        ├── models/
        └── uploads/
```

---

## 🛠️ Uso

### Comandos Make (Recomendado)

```bash
# Ver todos os comandos disponíveis
make help

# Build e deploy
make build          # Build das imagens
make up            # Inicia containers
make down          # Para containers
make restart       # Reinicia containers

# Logs
make logs          # Todos os logs
make logs-app      # Logs da aplicação
make logs-nginx    # Logs do Nginx

# Shell
make shell         # Shell da aplicação
make shell-db      # Shell do PostgreSQL

# Database
make db-init       # Inicializa banco
make db-backup     # Backup do banco
make backup        # Backup completo

# Desenvolvimento
make dev           # Modo desenvolvimento
make watch         # Hot-reload

# Monitoramento
make monitoring-up # Prometheus + Grafana
make admin-up      # PgAdmin
```

### Comandos Docker Compose

```bash
# Iniciar todos os serviços
docker-compose up -d

# Parar todos os serviços
docker-compose down

# Ver logs
docker-compose logs -f app

# Executar comando no container
docker-compose exec app python manage.py

# Rebuild de um serviço específico
docker-compose up -d --build app
```

---

## 🌐 Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Página inicial |
| `/health` | GET | Health check |
| `/api/analyze` | POST | Análise de imagem |
| `/api/history` | GET | Histórico de análises |
| `/upload` | POST | Upload de imagem |

### Exemplo de Uso da API

```bash
# Health check
curl http://localhost/health

# Upload e análise de imagem
curl -X POST \
  -F "image=@skin_lesion.jpg" \
  http://localhost/api/analyze
```

---

## 🚀 Produção

### 1. Configurar SSL/TLS

#### Opção A: Let's Encrypt (Gratuito)

```bash
# Instalar certbot
apt-get install certbot

# Gerar certificado
certbot certonly --standalone -d seu-dominio.com

# Copiar certificados
cp /etc/letsencrypt/live/seu-dominio.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/seu-dominio.com/privkey.pem ssl/
```

#### Opção B: Certificado Próprio

```bash
# Gerar certificado auto-assinado (apenas para testes)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/privkey.pem \
  -out ssl/fullchain.pem
```

### 2. Editar nginx.conf

Descomente a seção HTTPS no `nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name seu-dominio.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # ... resto da configuração
}
```

### 3. Configurar Firewall

```bash
# UFW (Ubuntu)
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Firewalld (CentOS/RHEL)
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

### 4. Deploy em Produção

```bash
# Usar variáveis de produção
cp .env.example .env.production
nano .env.production  # Configurar variáveis

# Deploy
make prod-deploy

# Verificar logs
make prod-logs
```

### 5. Backup Automatizado

```bash
# Criar cron job para backup diário
crontab -e

# Adicionar linha:
0 2 * * * cd /path/to/Skin-cancer-Analyzer && make backup
```

---

## 📊 Monitoramento

### Prometheus + Grafana

```bash
# Iniciar stack de monitoramento
make monitoring-up

# Acessar Prometheus
# http://localhost:9090

# Acessar Grafana
# http://localhost:3000
# Usuário: admin
# Senha: admin
```

### PgAdmin (Administração do Banco)

```bash
# Iniciar PgAdmin
make admin-up

# Acessar
# http://localhost:5050
# Email: admin@skincancer.local
# Senha: admin
```

---

## 🔧 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs app

# Verificar status
docker-compose ps

# Rebuild forçado
docker-compose build --no-cache app
docker-compose up -d app
```

### Erro de permissão

```bash
# Ajustar permissões
sudo chown -R $USER:$USER uploads/ logs/
chmod -R 755 uploads/ logs/
```

### Modelo não carrega

```bash
# Verificar se modelo existe
ls -lh models/skin_cancer_model.h5

# Ver logs de carregamento
docker-compose logs app | grep -i model

# Copiar modelo para container
docker cp models/skin_cancer_model.h5 skin_cancer_app:/app/models/
```

### Banco de dados não conecta

```bash
# Verificar se PostgreSQL está rodando
docker-compose ps postgres

# Testar conexão
docker-compose exec app python -c "from app import db; print(db.engine.url)"

# Reiniciar banco
docker-compose restart postgres
```

### Alto uso de memória

```bash
# Ver uso de recursos
docker stats

# Limitar recursos no docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

### Limpar cache e rebuild

```bash
# Limpar tudo
make clean

# Rebuild do zero
make rebuild
```

---

## 🧪 Desenvolvimento

### Hot Reload

```bash
# Modo desenvolvimento com auto-reload
make dev
```

### Executar Testes

```bash
# Testes unitários
make test

# Testes com coverage
make test-coverage
```

### Adicionar Dependências

```bash
# Editar requirements.txt
nano requirements.txt

# Rebuild
make rebuild
```

---

## 📝 Logs

### Localização dos Logs

- **Aplicação**: `logs/app.log`
- **Nginx**: Container logs via `docker-compose logs nginx`
- **PostgreSQL**: Container logs via `docker-compose logs postgres`

### Ver logs em tempo real

```bash
# Todos os serviços
make logs

# Apenas aplicação
make logs-app

# Nginx
make logs-nginx
```

---

## 🔒 Segurança

### Checklist de Segurança

- [ ] Alterar `SECRET_KEY` em produção
- [ ] Usar senha forte para PostgreSQL
- [ ] Configurar SSL/TLS
- [ ] Habilitar CORS apenas para domínios confiáveis
- [ ] Configurar rate limiting no Nginx
- [ ] Manter dependências atualizadas
- [ ] Fazer backup regularmente
- [ ] Monitorar logs de acesso
- [ ] Usar firewall
- [ ] Scan de vulnerabilidades: `make scan`

---

## 📚 Recursos Adicionais

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

---

## 🤝 Suporte

Para dúvidas ou problemas:

1. Consulte o [Troubleshooting](#troubleshooting)
2. Verifique os [logs](#logs)
3. Abra uma issue no GitHub

---

## 📄 Licença

Este projeto está sob a licença especificada no repositório.

---

**Desenvolvido com ❤️ por VerticalAgent**
