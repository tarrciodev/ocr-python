FROM python:3.13-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório da aplicação
WORKDIR /app
COPY . /app

# Instalar dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expor porta para Render
EXPOSE 10000

# Rodar FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
