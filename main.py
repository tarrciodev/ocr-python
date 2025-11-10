from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from app.utils.pdf_reader import extract_text_from_pdf  # updated import
import tempfile
import os

app = FastAPI(
    title="OCR PDF API",
    description="API para extrair texto de faturas PDF (digitais ou escaneadas)",
    version="1.0.0"
)

# Permitir CORS (para usar com front-end ou Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "✅ API OCR PDF em execução!"}


@app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    """
    Extrai texto de um arquivo PDF enviado (aceita PDFs com imagem ou texto digital).
    """
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = extract_text_from_pdf(tmp_path)
        return {"success": True, "filename": file.filename, "text": text}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        os.remove(tmp_path)
