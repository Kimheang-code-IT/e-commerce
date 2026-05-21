# API is served on 8000 inside the stack; docker-compose adds workers/proxy-headers. Public HTTP(S) is nginx only.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Invoice PDFs and product images (shared with celery-worker via compose volume)
RUN mkdir -p /app/uploads/invoices /app/uploads/products

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
