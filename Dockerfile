FROM python:3.12-slim

WORKDIR /app

# Install Node.js (needed for twikit's enable_ui_metrics)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    npm install -g jsdom && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Initialize DB on first run if it doesn't exist
CMD ["sh", "-c", "python -m db.init_db && python main.py"]
