from fastapi import FastAPI, File, UploadFile, Body
from fastapi.responses import JSONResponse
import os
import tempfile
import time
import re

from app.utils.pdf_reader import extract_text_from_pdf, is_pdf_scanned

app = FastAPI(
    title="API OCR de Faturas",
    description="Extrai texto de PDFs (digitais ou escaneados) com Tesseract + OpenCV + PyMuPDF e analisa faturas",
    version="2.2.0"
)

@app.get("/")
def root():
    return {"status": "ok", "message": "API OCR de Faturas está a funcionar 🚀"}

@app.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    start_time = time.time()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        scanned = is_pdf_scanned(tmp_path)
        extracted_text = extract_text_from_pdf(tmp_path)
        text_length = len(extracted_text)

        file_info = {
            "filename": file.filename,
            "file_size": os.path.getsize(tmp_path),
            "is_scanned": scanned,
            "text_length": text_length,
            "extracted_text": extracted_text
        }

        duration = round(time.time() - start_time, 2)
        return JSONResponse({
            "success": True,
            "processing_time": f"{duration}s",
            **file_info
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/analyze-text")
async def analyze_text_endpoint(payload: dict = Body(...)):
    """
    Recebe JSON: {"text": "conteúdo extraído do PDF"}
    Retorna um array de faturas separadas.
    """
    text = payload.get("text")
    if not text:
        return JSONResponse({
            "success": False,
            "error": "Campo 'text' é obrigatório no JSON."
        }, status_code=400)

    def parse_faturas(text: str):
        faturas = re.split(r'(FT \d{4}/\d+)', text)
        resultados = []

        i = 1
        while i < len(faturas):
            numdoc = faturas[i].strip()
            corpo = faturas[i + 1] if i + 1 < len(faturas) else ""

            date_match = re.search(r'(\d{2}-\d{2}-\d{4})', corpo)
            date = date_match.group(1) if date_match else None

            valor_match = re.search(r'Valor Pago: ([\d\.,]+) Kz', corpo)
            valor = valor_match.group(1).replace('.', '').replace(',', '.') if valor_match else None

            nif_match = re.search(r'NIF: (\d+)', corpo)
            nif_cliente = nif_match.group(1) if nif_match else None

            descricao = corpo.strip()[:150]

            resultados.append({
                "numdoc": numdoc,
                "date": date,
                "valor": valor,
                "nif_cliente": nif_cliente,
                "descricao": descricao
            })
            i += 2

        return resultados

    try:
        faturas_array = parse_faturas(text)
        return {"success": True, "faturas": faturas_array}

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
