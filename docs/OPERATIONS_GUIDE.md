# APIC Operations Guide

## Overview

This guide is for DevOps engineers, system administrators, and platform teams responsible for deploying, maintaining, and monitoring APIC in production environments.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Management](#database-management)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup & Recovery](#backup--recovery)
7. [Security Hardening](#security-hardening)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance Procedures](#maintenance-procedures)
10. [Disaster Recovery](#disaster-recovery)

---

## Deployment Options

### Option 1: Docker Compose (Recommended for Small Deployments)

```bash
# Quick start
docker-compose up -d

# With build
docker-compose up -d --build
```

**Services Started:**
| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| PostgreSQL | apic-postgres | 5432 | Relational database |
| FastAPI | apic-api | 8000 | Backend API |
| Streamlit | apic-frontend | 8501 | Web interface |

### Option 2: Kubernetes (Production)

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apic-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: apic-api
  template:
    metadata:
      labels:
        app: apic-api
    spec:
      containers:
      - name: api
        image: apic:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: apic-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### Option 3: Manual Installation (Development)

```bash
# Using setup script
./scripts/setup.sh --full

# Or using Makefile
make install
```

---

## Installation

### Prerequisites

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4GB | 8GB+ |
| Storage | 20GB | 50GB+ SSD |
| Python | 3.11 | 3.11+ |
| PostgreSQL | 15 | 15+ |

### System Dependencies

**Ubuntu/Debian:**
```bash
apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql-client \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    build-essential
```

**RHEL/CentOS:**
```bash
yum install -y \
    python311 \
    python311-pip \
    postgresql15 \
    poppler-utils \
    tesseract
```

**macOS:**
```bash
brew install \
    python@3.11 \
    postgresql@15 \
    poppler \
    tesseract
```

### Automated Installation

```bash
# Clone repository
git clone https://github.com/your-org/APIC.git
cd APIC

# Run automated setup
./scripts/setup.sh --full

# Verify installation
make health-check
```

### Docker Installation

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## Configuration

### Environment Variables

Create `.env` file from template:

```bash
cp .env.example .env
```

**Required Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/apic` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `PINECONE_API_KEY` | Pinecone API key | `pcsk_...` |
| `PINECONE_ENVIRONMENT` | Pinecone region | `us-east-1` |

**Optional Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |
| `STREAMLIT_PORT` | `8501` | Frontend port |
| `MAX_FILE_SIZE_MB` | `50` | Max upload size |
| `LLM_TEMPERATURE` | `0.7` | LLM creativity |

### Configuration File

`config/settings.py` uses Pydantic for validation:

```python
class Settings(BaseSettings):
    # Application
    APP_NAME: str = "APIC"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5

    # LLM
    DEFAULT_LLM_PROVIDER: str = "openai"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096

    class Config:
        env_file = ".env"
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-apic}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      target: api
    environment:
      - DATABASE_URL=${DATABASE_URL:-postgresql://postgres:postgres@postgres:5432/apic}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./reports:/app/reports
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: .
      target: frontend
    environment:
      - API_BASE_URL=http://api:8000/api/v1
    depends_on:
      - api

volumes:
  postgres_data:
```

---

## Database Management

### Initial Setup

```bash
# Using Makefile
make db-init

# Or using script
python scripts/init_db.py

# Check tables
python scripts/init_db.py --check
```

### Connection Pooling (Production)

Use PgBouncer for connection pooling:

```ini
# pgbouncer.ini
[databases]
apic = host=postgres port=5432 dbname=apic

[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
```

### Database Migrations

Using Alembic for schema migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Performance Tuning

```sql
-- PostgreSQL configuration recommendations
-- /etc/postgresql/15/main/postgresql.conf

# Memory
shared_buffers = 256MB
work_mem = 16MB
maintenance_work_mem = 128MB

# Connections
max_connections = 100

# Logging
log_min_duration_statement = 1000  # Log slow queries (>1s)

# Autovacuum
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05
```

### Useful Queries

```sql
-- Check project states
SELECT project_id, current_node, is_suspended, updated_at
FROM project_states
ORDER BY updated_at DESC;

-- Count documents by project
SELECT p.project_name, COUNT(d.id) as doc_count
FROM projects p
LEFT JOIN documents d ON p.id = d.project_id
GROUP BY p.id, p.project_name;

-- Find suspended projects
SELECT p.client_name, p.project_name, ps.suspension_reason, ps.updated_at
FROM project_states ps
JOIN projects p ON ps.project_id = p.id
WHERE ps.is_suspended = true;
```

---

## Monitoring & Logging

### Application Logging

```python
# Logging configuration
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/apic.log"),
        logging.StreamHandler()
    ]
)
```

**Log Levels:**
| Level | Usage |
|-------|-------|
| DEBUG | Detailed debugging info |
| INFO | General operations |
| WARNING | Unexpected but handled |
| ERROR | Errors requiring attention |
| CRITICAL | System failures |

### Log Aggregation

**Example: Loki + Grafana**

```yaml
# docker-compose with Loki
services:
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - ./logs:/var/log/apic
      - ./promtail-config.yaml:/etc/promtail/config.yml
```

### Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-01-21T10:30:00Z"
}
```

**Docker health check:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Metrics (Future)

```python
# Prometheus metrics example
from prometheus_client import Counter, Histogram

# Request counter
requests_total = Counter(
    'apic_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

# Request latency
request_latency = Histogram(
    'apic_request_latency_seconds',
    'Request latency',
    ['endpoint']
)
```

---

## Backup & Recovery

### Database Backup

**Daily backup script:**
```bash
#!/bin/bash
# backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/apic"
DB_URL="postgresql://postgres:postgres@localhost:5432/apic"

mkdir -p $BACKUP_DIR

# Full backup
pg_dump $DB_URL > $BACKUP_DIR/apic_full_$DATE.sql

# Compressed backup
pg_dump $DB_URL | gzip > $BACKUP_DIR/apic_full_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "apic_full_*.sql*" -mtime +7 -delete

echo "Backup completed: apic_full_$DATE.sql.gz"
```

**Cron job:**
```bash
# Run daily at 2 AM
0 2 * * * /opt/apic/scripts/backup_db.sh >> /var/log/apic-backup.log 2>&1
```

### File Backup

```bash
#!/bin/bash
# backup_files.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/apic"

# Backup uploads and reports
tar -czf $BACKUP_DIR/apic_files_$DATE.tar.gz \
    /opt/apic/uploads \
    /opt/apic/reports

# Keep only last 7 days
find $BACKUP_DIR -name "apic_files_*.tar.gz" -mtime +7 -delete
```

### Restore Procedures

**Database restore:**
```bash
# Stop application
docker-compose stop api frontend

# Restore database
psql $DB_URL < /backups/apic/apic_full_20260121_020000.sql

# Start application
docker-compose start api frontend
```

**File restore:**
```bash
# Restore files
tar -xzf /backups/apic/apic_files_20260121_020000.tar.gz -C /
```

---

## Security Hardening

### Network Security

```yaml
# docker-compose.yml - Network isolation
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

services:
  postgres:
    networks:
      - backend  # Only internal

  api:
    networks:
      - frontend
      - backend

  frontend:
    networks:
      - frontend
```

### Environment Security

```bash
# Secure .env file
chmod 600 .env
chown apic:apic .env

# Use secrets management in production
# Example: Docker secrets
echo "your-api-key" | docker secret create openai_api_key -
```

### API Security

```nginx
# Nginx reverse proxy with rate limiting
upstream apic_api {
    server 127.0.0.1:8000;
}

limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 443 ssl http2;
    server_name apic.example.com;

    ssl_certificate /etc/ssl/certs/apic.crt;
    ssl_certificate_key /etc/ssl/private/apic.key;

    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://apic_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Database Security

```sql
-- Create application user with limited permissions
CREATE USER apic_app WITH PASSWORD 'secure_password';

GRANT CONNECT ON DATABASE apic TO apic_app;
GRANT USAGE ON SCHEMA public TO apic_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO apic_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO apic_app;

-- Revoke dangerous permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
psql postgresql://postgres:postgres@localhost:5432/apic

# Check network
docker-compose exec api ping postgres
```

**2. LLM API Errors**
```bash
# Verify API keys are set
docker-compose exec api env | grep API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**3. Document Upload Failures**
```bash
# Check upload directory permissions
ls -la uploads/

# Check disk space
df -h

# Check file size limits
grep MAX_FILE_SIZE .env
```

**4. Out of Memory**
```bash
# Check container memory usage
docker stats

# Increase memory limits
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
```

### Debug Mode

```bash
# Enable debug mode
export DEBUG=true

# Run with verbose logging
python main.py api

# Check logs
tail -f logs/apic.log
```

### Container Debugging

```bash
# Shell into container
docker-compose exec api /bin/bash

# Check processes
docker-compose exec api ps aux

# Check network
docker-compose exec api netstat -tlnp

# View real-time logs
docker-compose logs -f api
```

---

## Maintenance Procedures

### Regular Maintenance

**Daily:**
- Review error logs
- Check disk usage
- Verify backups completed

**Weekly:**
- Analyze database performance
- Review slow query logs
- Check for security updates

**Monthly:**
- Test disaster recovery
- Review and rotate logs
- Update dependencies

### Upgrading APIC

```bash
# 1. Backup database and files
./scripts/backup_db.sh
./scripts/backup_files.sh

# 2. Pull latest code
git fetch origin
git checkout v1.2.0

# 3. Rebuild containers
docker-compose build

# 4. Run migrations
docker-compose exec api alembic upgrade head

# 5. Restart services
docker-compose up -d

# 6. Verify health
make health-check
```

### Database Maintenance

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Reindex if needed
REINDEX DATABASE apic;

-- Check table sizes
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Log Rotation

```bash
# /etc/logrotate.d/apic
/opt/apic/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 apic apic
    postrotate
        docker-compose -f /opt/apic/docker-compose.yml restart api > /dev/null
    endscript
}
```

---

## Disaster Recovery

### Recovery Time Objective (RTO)

| Scenario | Target RTO |
|----------|-----------|
| Database failure | < 1 hour |
| Container failure | < 15 minutes |
| Full system failure | < 4 hours |

### Recovery Procedures

**Database Recovery:**
```bash
# 1. Stop application
docker-compose stop api frontend

# 2. Start fresh PostgreSQL
docker-compose up -d postgres

# 3. Restore from backup
psql $DB_URL < /backups/apic/latest.sql

# 4. Verify data
psql $DB_URL -c "SELECT COUNT(*) FROM projects;"

# 5. Restart application
docker-compose start api frontend
```

**Full System Recovery:**
```bash
# 1. Provision new server
# 2. Install Docker and docker-compose
# 3. Clone repository
git clone https://github.com/your-org/APIC.git

# 4. Copy environment file
scp backup_server:/backups/apic/.env .env

# 5. Restore database
docker-compose up -d postgres
psql $DB_URL < /backups/apic/latest.sql

# 6. Restore files
tar -xzf /backups/apic/apic_files_latest.tar.gz -C .

# 7. Start application
docker-compose up -d
```

### Testing Recovery

```bash
# Monthly DR test procedure
# 1. Create test environment
docker-compose -f docker-compose.test.yml up -d

# 2. Restore backup
psql $TEST_DB_URL < /backups/apic/latest.sql

# 3. Run health checks
curl http://localhost:8001/health

# 4. Verify data integrity
psql $TEST_DB_URL -c "SELECT COUNT(*) FROM projects;"

# 5. Cleanup
docker-compose -f docker-compose.test.yml down -v
```

---

## Appendix

### Useful Commands

```bash
# Service management
make docker-up          # Start all services
make docker-down        # Stop all services
make docker-logs        # View logs
make docker-restart     # Restart services

# Database
make db-init            # Initialize database
make db-migrate         # Run migrations
make db-reset           # Reset database (DESTRUCTIVE)

# Health
make health-check       # Run health checks
make test               # Run tests

# Cleanup
make clean              # Clean caches
make clean-all          # Clean including venv
```

### Contact Information

For critical issues:
- On-call rotation: [Your PagerDuty/OpsGenie]
- Escalation: [Team lead contact]
- Vendor support: [Pinecone/OpenAI support links]
