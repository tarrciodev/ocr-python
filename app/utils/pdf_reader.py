import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
import subprocess
import cv2
import numpy as np

def check_tesseract_installation() -> bool:
    """Verifica se o Tesseract está instalado"""
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, text=True, timeout=5)
        return True
    except Exception:
        return False


def extract_text_from_pdf(file_path: str) -> str:
    """Extrai texto de PDF digital ou escaneado (com OCR aprimorado)."""
    if not check_tesseract_installation():
        return "Tesseract OCR não está instalado corretamente."

    text = ""
    with fitz.open(file_path) as pdf:
        total_pages = len(pdf)
        print(f"📄 PDF aberto com {total_pages} páginas.")

        for i, page in enumerate(pdf):
            print(f"🔍 Processando página {i + 1}/{total_pages}...")
            page_text = page.get_text("text")

            if has_significant_text(page_text):
                print("✅ Texto detectado diretamente (sem OCR).")
                text += f"\n\n===== Página {i+1} =====\n{page_text.strip()}"
            else:
                print("⚙️ Página parece ser imagem — aplicando OCR avançado...")
                text += f"\n\n===== Página {i+1} (OCR) =====\n"
                text += ocr_page(page)

    print("✅ Extração concluída.")
    return text.strip()


def ocr_page(page) -> str:
    """Executa OCR em uma página PDF com OpenCV e Tesseract (por+eng)."""
    try:
        # Converter página em imagem de alta resolução
        zoom = 3.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")

        # Ler imagem com OpenCV
        img_array = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        # Converter para escala de cinza
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Remover ruído e suavizar bordas
        gray = cv2.bilateralFilter(gray, 9, 75, 75)

        # Aumentar contraste (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Binarização adaptativa
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            35, 11
        )

        # Converter para PIL (necessário para pytesseract)
        pil_image = Image.fromarray(thresh)

        # Configuração avançada do Tesseract
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        text = pytesseract.image_to_string(pil_image, lang="por+eng", config=custom_config)

        return clean_text(text)

    except Exception as e:
        print(f"❌ Erro no OCR da página: {e}")
        return f"[Erro OCR: {e}]"


def has_significant_text(text: str, min_words: int = 5) -> bool:
    """Verifica se o texto contém informação significativa."""
    return bool(text and len(text.strip().split()) >= min_words)


def clean_text(text: str) -> str:
    """Limpa ruídos comuns e formata o texto OCR."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([|])', 'I', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # remove símbolos especiais invisíveis
    return text.strip()


def is_pdf_scanned(file_path: str) -> bool:
    """Verifica se o PDF é escaneado (sem texto real)."""
    try:
        with fitz.open(file_path) as pdf:
            for page in pdf[:2]:  # verifica as 2 primeiras páginas
                if has_significant_text(page.get_text("text")):
                    return False
        return True
    except Exception:
        return True
