#!/usr/bin/env bash
# Start the PostgreSQL MCP server for Claude Code.
# Loads DATABASE_URL from .env if not already set in the environment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -f "$PROJECT_ROOT/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$PROJECT_ROOT/.env"
  set +a
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set." \
       "Add it to .env or export it before starting Claude Code." >&2
  exit 1
fi

exec npx -y @modelcontextprotocol/server-postgres "$DATABASE_URL"
