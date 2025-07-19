FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y build-essential \
 && pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
