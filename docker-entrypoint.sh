#!/bin/bash
# Helper script for Docker operations

set -e

case "$1" in
  load-csv)
    echo "Loading fund_labels CSV into database..."
    docker-compose exec postgres psql -U ${POSTGRES_USER:-fintela} -d ${POSTGRES_DB:-fintela} <<EOF
\COPY fund_labels FROM '/docker-entrypoint-initdb.d/fund_labels_202511180330.csv' WITH CSV HEADER;
EOF
    echo "✅ CSV loaded successfully"
    ;;
  create-portfolios)
    echo "Creating test portfolios..."
    docker-compose exec fastapi uv run python create_test_portfolios.py
    echo "✅ Portfolios created"
    ;;
  logs)
    docker-compose logs -f "${2:-}"
    ;;
  shell-fastapi)
    docker-compose exec fastapi bash
    ;;
  shell-postgres)
    docker-compose exec postgres psql -U ${POSTGRES_USER:-fintela} -d ${POSTGRES_DB:-fintela}
    ;;
  *)
    echo "Usage: $0 {load-csv|create-portfolios|logs [service]|shell-fastapi|shell-postgres}"
    exit 1
    ;;
esac

