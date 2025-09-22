FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY investment_manager.py .

EXPOSE 8080

CMD ["python", "investment_manager.py"]
