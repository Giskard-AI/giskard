#! /usr/bin/env bash
# prestart.sh is executed by uvicorn-gunicorn-fastapi-docker. The name is default by convention.

# Let the DB start
python /app/app/backend_pre_start.py

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head
echo "Done"

# Generate email templates from MJML
bash ./scripts/email-templates.sh

# Create initial data in DB
python /app/app/initial_data.py
