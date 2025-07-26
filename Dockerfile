# Dockerfile

FROM --platform=linux/amd64 python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY utils/ ./utils/
COPY main.py ./

CMD ["python", "main.py"]