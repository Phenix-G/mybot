# Build stage
FROM python:3.12-alpine as builder

WORKDIR /app

# Copy only the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-alpine

WORKDIR /app

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Install netcat for database check
# RUN apk add --no-cache netcat-openbsd

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/scripts/entrypoint.sh

# Start the application
CMD ["/app/scripts/entrypoint.sh"]
