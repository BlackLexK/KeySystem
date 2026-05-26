FROM python:3.12-slim

RUN apt-get update && apt-get install -y     python3-tk     tk-dev     libsqlite3-dev     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
COPY setup.py .
COPY main.py .
COPY auth.py .
COPY gui.py .
COPY models.py .
COPY services.py .
COPY database.py .
COPY utils.py .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

ENV DB_DIR=/app/data
ENV DB_PATH=/app/data/D1.db
RUN mkdir -p /app/data

CMD ["keycontrol"]
