FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema (incluindo libGL para OpenCV)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]