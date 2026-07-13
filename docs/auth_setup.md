# Authentication Setup & Runbook

Guide to configuring database setups, keys, and schemas for Phase 2.

## Config Options

Configure the following variables in your local `.env` configuration file:

```bash
# JWT secrets configuration parameters
JWT_SECRET=super-secure-jwt-secret-key-32-chars-long
JWT_EXPIRES_IN=3600

# Cache configurations
REDIS_URL=redis://localhost:6379

# Relational persistence parameters
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aegis_db?sslmode=disable
```

## Migration Guide

To run database migrations using Alembic:

```bash
# Upgrade database to head revision
alembic upgrade head
```
