# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app
ENV FLASK_ENV=development

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
RUN pip install --no-cache-dir -r requirements.txt

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

# Create necessary directories
RUN mkdir -p /app/static/charts /app/static/reports /app/uploads

# Set permissions
RUN chmod +x /app/run.py

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "run.py"] 