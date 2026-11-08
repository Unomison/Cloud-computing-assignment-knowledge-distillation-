FROM python:3.11-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install CPU-only PyTorch and pinned requirements
RUN pip install --no-cache-dir torch==2.2.2+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir transformers==4.39.3 boto3==1.34.84 pydantic==2.6.4

# Copy service application code (no weights included in image)
COPY service/app.py /app/app.py
COPY data/schema.json /app/schema.json

# Default runtime configuration
ENV PORT=8000 \
    MODEL_URI=models/v1 \
    MODEL_VERSION=v1 \
    S3_ENDPOINT=http://seaweedfs-s3.data.svc.cluster.local:8333 \
    MAX_NEW_TOKENS=64 \
    FAULT_INJECT=0

EXPOSE 8000

# Non-root user for security best practices
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

CMD ["python", "app.py"]

