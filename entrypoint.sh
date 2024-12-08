#!/bin/sh

echo "Waiting for MySQL to be ready..."
while ! nc -z ${MYSQL_HOST:-mysql} ${MYSQL_PORT:-3306}; do
    echo "MySQL is unavailable - sleeping"
    sleep 1
done
echo "MySQL is up - executing migrations"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Wait for Redis
echo "Waiting for Redis to be ready..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done
echo "Redis is up - starting application"

# Start the application
echo "Starting the application..."
python main.py 