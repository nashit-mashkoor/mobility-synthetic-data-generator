FROM python:3.9-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Pin setuptools to version compatible with legacy setup.py packages
RUN pip install --no-cache-dir pip==23.0.1 setuptools==65.5.0 wheel

# Install dependencies into virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Production Stage ---
FROM python:3.9-slim

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install runtime dependencies and create machine-id for Streamlit metrics
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dbus \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/archives/* \
    && dbus-uuidgen > /etc/machine-id

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup . .

# Create writable directories for Streamlit and Matplotlib
RUN mkdir -p /home/appuser/.streamlit \
    /home/appuser/.config/matplotlib \
    /home/appuser/.cache \
    && chown -R appuser:appgroup /home/appuser

# Security: Set proper permissions
RUN chmod -R 755 /app && \
    find /app -type f -exec chmod 644 {} \;

# Security: Switch to non-root user
USER appuser

# Use virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

# Set matplotlib config directory
ENV MPLCONFIGDIR="/home/appuser/.config/matplotlib"

# Security: Streamlit production settings
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_FILE_WATCHER_TYPE=none \
    STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8501/ || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
