# ─────────────────────────────────────────────────────────────────────────────
# ViralFlux — Docker Compose Makefile
# Usage: make <target>
# ─────────────────────────────────────────────────────────────────────────────

# ANSI color codes
RESET   := \033[0m
BOLD    := \033[1m
GREEN   := \033[32m
CYAN    := \033[36m
YELLOW  := \033[33m
RED     := \033[31m

COMPOSE := docker compose

.PHONY: help up down logs logs-worker logs-beat migrate shell-backend shell-frontend shell-db build restart ps seed

## help: Show this help message
help:
	@printf "$(BOLD)$(CYAN)ViralFlux — available targets$(RESET)\n"
	@printf "$(CYAN)─────────────────────────────────────────────────$(RESET)\n"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf "$(CYAN)─────────────────────────────────────────────────$(RESET)\n"

## up: Start all services in detached mode
up:
	@printf "$(BOLD)$(GREEN)Starting ViralFlux services...$(RESET)\n"
	$(COMPOSE) up -d
	@printf "$(GREEN)All services started.$(RESET)\n"

## down: Stop and remove all containers (preserves volumes)
down:
	@printf "$(BOLD)$(YELLOW)Stopping ViralFlux services...$(RESET)\n"
	$(COMPOSE) down
	@printf "$(YELLOW)All services stopped.$(RESET)\n"

## build: Build (or rebuild) all Docker images
build:
	@printf "$(BOLD)$(CYAN)Building Docker images...$(RESET)\n"
	$(COMPOSE) build --no-cache
	@printf "$(GREEN)Build complete.$(RESET)\n"

## restart: Restart all services
restart:
	@printf "$(BOLD)$(YELLOW)Restarting all services...$(RESET)\n"
	$(COMPOSE) restart
	@printf "$(GREEN)All services restarted.$(RESET)\n"

## logs: Follow log output for all services (Ctrl-C to exit)
logs:
	$(COMPOSE) logs -f

## logs-worker: Follow Celery worker logs (video generation tasks)
logs-worker:
	$(COMPOSE) logs -f worker

## logs-beat: Follow Celery beat scheduler logs (scan_schedules, sync_analytics)
logs-beat:
	$(COMPOSE) logs -f beat

## ps: Show status of all running containers
ps:
	$(COMPOSE) ps

## migrate: Run Alembic database migrations inside the backend container
migrate:
	@printf "$(BOLD)$(CYAN)Running database migrations...$(RESET)\n"
	$(COMPOSE) exec backend alembic upgrade head
	@printf "$(GREEN)Migrations complete.$(RESET)\n"

## seed: Run the database seed script inside the backend container
seed:
	@printf "$(BOLD)$(CYAN)Seeding database...$(RESET)\n"
	$(COMPOSE) exec backend python -m app.seed
	@printf "$(GREEN)Database seeded.$(RESET)\n"

## shell-backend: Open an interactive shell inside the backend container
shell-backend:
	@printf "$(BOLD)$(CYAN)Opening shell in backend container...$(RESET)\n"
	$(COMPOSE) exec backend /bin/bash

## shell-frontend: Open an interactive shell inside the frontend container
shell-frontend:
	@printf "$(BOLD)$(CYAN)Opening shell in frontend container...$(RESET)\n"
	$(COMPOSE) exec frontend /bin/sh

## shell-db: Open a psql session inside the postgres container
shell-db:
	@printf "$(BOLD)$(CYAN)Opening psql session...$(RESET)\n"
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}
