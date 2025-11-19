FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and set timezone
RUN apt-get update && apt-get install -y \
    gcc \
    tzdata \
    && ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && echo "Asia/Tokyo" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY api/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ .

# Expose port
EXPOSE 8000

# Run migrations and start the application
CMD ["sh", "-c", "cd /app/api && python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
