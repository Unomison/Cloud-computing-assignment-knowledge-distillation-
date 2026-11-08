FROM python:3.11-slim
WORKDIR /app
COPY worker/worker.py /app/worker.py
COPY prompts /app/prompts
COPY data /app/data
CMD ["python", "worker.py"]

