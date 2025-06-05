FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY consumer/ ./consumer/

EXPOSE 8000

CMD ["python", "consumer/app.py"]