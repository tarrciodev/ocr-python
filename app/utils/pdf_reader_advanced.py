import fitz  # PyMuPDF
import re

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrai texto do PDF usando métodos avançados do PyMuPDF.
    Não requer OCR externo.
    """
    text = ""
    try:
        with fitz.open(file_path) as pdf:
            print(f"PDF aberto: {len(pdf)} páginas")
            
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                print(f"Processando página {page_num + 1}...")
                
                # Usa método avançado de extração
                page_text = extract_text_advanced(page)
                
                if page_text and has_significant_text(page_text):
                    text += f"===== Page {page_num + 1} =====\n{page_text}\n\n"
                else:
                    text += f"===== Page {page_num + 1} =====\n[Pouco texto encontrado nesta página]\n\n"
                    
    except Exception as e:
        print(f"Erro ao extrair texto do PDF: {e}")
        return f"Erro na extração: {str(e)}"
    
    print(f"Extracção concluída: {len(text)} caracteres no total")
    return text

def extract_text_advanced(page) -> str:
    """
    Método avançado de extração de texto usando PyMuPDF.
    Combina múltiplas estratégias.
    """
    all_text = []
    
    # Estratégia 1: Extração normal de texto
    text_normal = page.get_text("text")
    if text_normal and has_significant_text(text_normal, min_words=2):
        all_text.append(("normal", text_normal))
    
    # Estratégia 2: Extração por palavras
    words = page.get_text("words")
    if words:
        text_words = " ".join([word[4] for word in words if isinstance(word[4], str) and word[4].strip()])
        if has_significant_text(text_words, min_words=2):
            all_text.append(("words", text_words))
    
    # Estratégia 3: Extração por blocos
    blocks = page.get_text("blocks")
    if blocks:
        text_blocks = "\n".join([block[4] for block in blocks if isinstance(block[4], str) and block[4].strip()])
        if has_significant_text(text_blocks, min_words=2):
            all_text.append(("blocks", text_blocks))
    
    # Estratégia 4: Extração por dicionário (mais detalhada)
    try:
        text_dict = page.get_text("dict")
        dict_text = extract_text_from_dict(text_dict)
        if has_significant_text(dict_text, min_words=2):
            all_text.append(("dict", dict_text))
    except:
        pass
    
    # Escolhe o melhor resultado
    if all_text:
        # Prefere o método que retornou mais texto
        best_method = max(all_text, key=lambda x: len(x[1]))
        print(f"Melhor método: {best_method[0]} com {len(best_method[1])} caracteres")
        return clean_text(best_method[1])
    
    return ""

def extract_text_from_dict(text_dict: dict) -> str:
    """
    Extrai texto da estrutura de dicionário do PyMuPDF.
    """
    text_parts = []
    
    if "blocks" in text_dict:
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    if "spans" in line:
                        for span in line["spans"]:
                            if "text" in span and span["text"].strip():
                                text_parts.append(span["text"])
    
    return " ".join(text_parts)

def clean_text(text: str) -> str:
    """
    Limpa e formata o texto extraído.
    """
    if not text:
        return ""
    
    # Remove múltiplos espaços
    text = re.sub(r'\s+', ' ', text)
    
    # Remove espaços no início e fim
    text = text.strip()
    
    # Corrige quebras de linha excessivas
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text

def has_significant_text(text: str, min_words: int = 2) -> bool:
    """
    Verifica se o texto extraído tem conteúdo significativo.
    """
    if not text:
        return False
    
    # Remove números isolados para evitar falsos positivos
    words = [word for word in text.strip().split() if not word.isdigit()]
    return len(words) >= min_words

def is_pdf_scanned(file_path: str) -> bool:
    """
    Verifica se o PDF é principalmente composto por imagens.
    """
    try:
        with fitz.open(file_path) as pdf:
            total_pages = len(pdf)
            text_pages = 0
            
            for page_num in range(min(3, total_pages)):
                page = pdf[page_num]
                text = page.get_text("text")
                
                if has_significant_text(text):
                    text_pages += 1
            
            return (text_pages / min(3, total_pages)) < 0.5
            
    except Exception as e:
        print(f"Erro ao verificar se PDF é scanned: {e}")
        return True