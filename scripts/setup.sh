#!/bin/bash
set -e

echo "🚀 Setting up Fintela project..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file"
    else
        echo "⚠️  .env.example not found. Please create .env manually."
    fi
fi

# Start Docker services
echo "📦 Starting Docker services..."
docker compose up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker compose exec -T postgres pg_isready -U ${POSTGRES_USER:-fintela} > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ PostgreSQL failed to start. Check logs with: docker compose logs postgres"
    exit 1
fi

# Wait a bit more for init scripts to run
echo "⏳ Waiting for database initialization..."
sleep 3

# Load CSV if needed
echo "📊 Loading fund_labels data..."
if command -v uv &> /dev/null; then
    uv run python scripts/init_db.py
else
    python scripts/init_db.py
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Services are running:"
echo "  📊 FastAPI:    http://localhost:8000"
echo "  🔄 Dagster:    http://localhost:3000"
echo "  📈 Dashboard:  http://localhost:5173"
echo ""
echo "Next steps:"
echo "  1. Run Dagster ingestion job to fetch fund data"
echo "  2. Create test portfolios: uv run python create_test_portfolios.py"
echo "  3. Check API docs: http://localhost:8000/docs"

