# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=wsgi:application
ENV FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        git \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for report generation
RUN pip install --no-cache-dir \
    matplotlib \
    seaborn \
    python-docx \
    pandas \
    openpyxl \
    xlsxwriter \
    pillow \
    qrcode[pil] \
    reportlab \
    python-socketio

# Copy project
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/static/charts /app/static/reports /app/static/exports /app/static/previews /app/uploads /app/templates \
    && chmod -R 755 /app/static /app/uploads /app/templates

# Expose port (Railway will set PORT env var)
EXPOSE ${PORT:-8080}

# Health check - use /api/health for quick liveness check
# Increased start period to 120 seconds for full app initialization
# Using longer timeouts to account for slow cloud deployments
HEALTHCHECK --interval=30s --timeout=20s --start-period=120s --retries=5 \
    CMD sh -c "curl -f http://localhost:\${PORT:-8080}/api/health || exit 1"

# Run with gunicorn for production
# Use shell form to properly expand PORT environment variable
# Increased workers and timeout for better stability
CMD sh -c "gunicorn wsgi:application --bind 0.0.0.0:\${PORT:-8080} --workers 4 --threads 2 --timeout 120 --access-logfile - --error-logfile - --log-level info"
