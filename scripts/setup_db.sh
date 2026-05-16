#!/bin/bash
# Setup local PostgreSQL database for development

set -e

DB_CONTAINER="soe-spotify-db"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_NAME="soe_spotify"
DB_PORT="5432"

echo "Setting up PostgreSQL database..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    echo "Container $DB_CONTAINER already exists."
    if docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
        echo "Container is running. Skipping creation."
    else
        echo "Starting existing container..."
        docker start $DB_CONTAINER
    fi
else
    echo "Creating new PostgreSQL container..."
    docker run --name $DB_CONTAINER \
        -e POSTGRES_USER=$DB_USER \
        -e POSTGRES_PASSWORD=$DB_PASSWORD \
        -e POSTGRES_DB=$DB_NAME \
        -p ${DB_PORT}:5432 \
        -d postgres:16

    echo "Waiting for database to be ready..."
    sleep 3
fi

# Test connection
echo "Testing database connection..."
PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null && \
    echo "Database is ready!" || \
    echo "Warning: Could not verify database connection"

echo ""
echo "Database setup complete!"
echo "Connection string: postgresql://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env (already has default connection)"
echo "2. Run: python -m soeSpotify.main"
echo "3. To stop: docker stop $DB_CONTAINER"
echo "4. To remove: docker rm $DB_CONTAINER"
