# Production Dockerfile for LangGraph Browser Agent
# Using official Microsoft Playwright image with all browser dependencies pre-configured
FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Chromium browser is installed and ready
RUN playwright install chromium

# Copy application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port for Web UI
EXPOSE 8080

# Default command
CMD ["python", "app.py"]