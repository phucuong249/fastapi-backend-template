#!/bin/bash

# Exit on error
set -e

# Load environment variables from .env
if [ -f .env ]; then
    # We need to expand variables like ${POSTGRES_USER} inside .env
    # A simple way is to treat it as a shell script if it's compatible, 
    # but let's be safer and read the keys we need.
    
    # Read basic credentials first
    # Use awk to handle potential quotes and whitespace
    export POSTGRES_USER=$(grep "^POSTGRES_USER=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | tr -d ' ')
    export POSTGRES_PASSWORD=$(grep "^POSTGRES_PASSWORD=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | tr -d ' ')
    export POSTGRES_DB=$(grep "^POSTGRES_DB=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | tr -d ' ')
    
    # Construct DATABASE_URL using Python to handle URL encoding of special characters
    export DATABASE_URL=$(python3 -c "
import os
import urllib.parse
user = urllib.parse.quote_plus(os.environ.get('POSTGRES_USER', ''))
password = urllib.parse.quote_plus(os.environ.get('POSTGRES_PASSWORD', ''))
db = os.environ.get('POSTGRES_DB', '')
host = 'localhost'
port = '5440'
print(f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}')
")
fi

# Check if required variables are set
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_DB" ]; then
    echo "Error: POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB must be set in .env"
    exit 1
fi

# Ensure Postgres container is running with latest config
echo "Ensuring PostgreSQL container is up-to-date..."
docker compose up -d postgres

echo "Waiting for PostgreSQL to be ready..."
until docker exec ai_backend_postgres pg_isready -U "$POSTGRES_USER"; do
    echo "Postgres is unavailable - sleeping"
    sleep 1
done

echo "PostgreSQL is up - executing command"

# Create database if it doesn't exist
# We use PGPASSWORD to avoid password prompt
export PGPASSWORD=$POSTGRES_PASSWORD

# Check if database exists
if docker exec -e PGPASSWORD=$PGPASSWORD ai_backend_postgres psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$POSTGRES_DB"; then
    echo "Database $POSTGRES_DB already exists"
else
    echo "Creating database $POSTGRES_DB..."
    docker exec -e PGPASSWORD=$PGPASSWORD ai_backend_postgres createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
    echo "Database $POSTGRES_DB created successfully"
fi

# Update password to match .env
echo "Updating database user password to match .env..."
docker exec ai_backend_postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER USER \"$POSTGRES_USER\" WITH PASSWORD '$POSTGRES_PASSWORD';"

# Run migrations
echo "Running Alembic migrations..."
./.venv/bin/alembic upgrade head

echo "Database setup completed successfully!"
