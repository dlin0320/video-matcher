FROM python:3.9.18-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "mock_consumer.py"]