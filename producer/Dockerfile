FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY producer/ ./producer/

EXPOSE 5000

CMD ["python", "producer/app.py"]