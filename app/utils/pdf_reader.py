# app/utils/pdf_reader.py
def extract_text_from_pdf(pdf_path):
    """
    Extrai texto de PDF usando PyMuPDF para PDFs digitais
    e pytesseract + pdf2image para PDFs com imagem
    """
    text = ""
    
    # 1. Primeiro tenta extração direta (PDFs digitais)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        if text.strip():
            return {
                "success": True, 
                "text": text, 
                "method": "pymupdf",
                "filename": pdf_path
            }
    except Exception as e:
        print(f"Erro na extração direta: {e}")
    
    # 2. Se não conseguiu texto, tenta OCR (PDFs com imagem)
    try:
        import pytesseract
        from PIL import Image
        import pdf2image
        
        # Converte PDF para imagens
        images = pdf2image.convert_from_path(pdf_path)
        
        ocr_text = ""
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image, lang='por')
            ocr_text += f"--- Página {i+1} ---\n{page_text}\n"
        
        if ocr_text.strip():
            return {
                "success": True, 
                "text": ocr_text, 
                "method": "ocr",
                "filename": pdf_path
            }
        else:
            return {
                "success": False, 
                "error": "Não foi possível extrair texto (OCR retornou vazio)",
                "filename": pdf_path
            }
            
    except Exception as e:
        return {
            "success": False, 
            "error": f"Erro no OCR: {str(e)}",
            "filename": pdf_path
        }