#!/bin/bash
# Creates the dedicated n8n database inside ViralFlux's own Postgres on first init.
# n8n (DB_POSTGRESDB_DATABASE=${N8N_DB_NAME:-n8n}) needs its own DB separate from
# the viralflux application DB. Runs only when the data dir is empty (fresh volume).
set -e

DBNAME="${N8N_DB_NAME:-n8n}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  SELECT 'CREATE DATABASE "$DBNAME"'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DBNAME')\gexec
EOSQL

echo "init-n8n-db: ensured database '$DBNAME' exists."
