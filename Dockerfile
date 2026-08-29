FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libzim-tools && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV ZIM_DIR=/zim
ENV PORT=8100

EXPOSE 8100

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]
