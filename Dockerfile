# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and static files
COPY app/ ./app/
COPY static/ ./static/

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Run the application (using module entry point)
CMD ["python", "-m", "app.main"]