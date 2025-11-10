import re
from datetime import datetime
from typing import List, Dict, Any

def parse_invoices(text: str) -> List[Dict[str, Any]]:
    """
    Analisa o texto do PDF e retorna um array JSON seguindo as regras fornecidas.
    Se nenhuma fatura for encontrada, retorna array com objeto vazio.
    """
    invoices = []
    
    # Primeiro, verifica se é uma fatura de combustível
    if is_gasoline_invoice(text):
        invoice = parse_gasoline_invoice(text, 1)
        if invoice:
            return [invoice]
    
    # Depois tenta identificar blocos de faturas
    fatura_blocks = split_invoice_blocks(text)
    
    if not fatura_blocks:
        return [create_empty_invoice()]
    
    for idx, block in enumerate(fatura_blocks, 1):
        invoice = parse_single_invoice(block, idx)
        if invoice:
            invoices.append(invoice)
    
    if not invoices:
        return [create_empty_invoice()]
    
    return invoices

def is_gasoline_invoice(text: str) -> bool:
    """Verifica se é uma fatura de combustível"""
    gasoline_indicators = [
        r'Sonangol',
        r'GASOLINA',
        r'Combustível',
        r'Bomba',
        r'Posto',
        r'Distribuidora'
    ]
    
    indicators_count = sum(1 for pattern in gasoline_indicators if re.search(pattern, text, re.IGNORECASE))
    return indicators_count >= 2

def parse_gasoline_invoice(text: str, order: int) -> Dict[str, Any]:
    """Analisa especificamente faturas de combustível da Sonangol"""
    # Extrair NIF da empresa (Sonangol)
    nif_empresa = extract_nif_empresa_sonangol(text)
    
    # Extrair NIF do cliente
    nif_cliente = extract_nif_cliente_sonangol(text)
    
    # Extrair número do documento
    numdoc = extract_numdoc_sonangol(text)
    
    # Extrair data
    date = extract_date_sonangol(text)
    
    # Extrair valor total
    valor = extract_valor_sonangol(text)
    
    # Extrair nome da empresa
    nome_empresa = "Sonangol Distribuidora"
    
    # Extrair nome do cliente (pode estar vazio)
    nome_cliente = extract_nome_cliente_sonangol(text)
    
    # Para faturas de combustível
    descricao = "Abastecimento de combustível"
    tipologia = "CM"  # Combustível
    iva = "0,00"
    valor_tributavel = valor
    retencao = "NÃO"  # Combustível não tem retenção
    retencao_valor = "0,00"
    
    # Determinar status - para combustível, o nome do cliente pode estar vazio
    status = "CUMPRE" if nif_empresa and nif_cliente and date and valor and numdoc else "NÃO CUMPRE"
    
    # Gerar análise
    analise = generate_gasoline_analysis(nome_empresa, nome_cliente, nif_cliente, valor, status)
    
    return {
        "analise": analise,
        "email": "",
        "regime": "Regime Geral",
        "nif_cliente": nif_cliente,
        "nif_empresa": nif_empresa,
        "num_ordem": str(order),
        "nome_cliente": nome_cliente,
        "nome_empresa": nome_empresa,
        "type_document": "FR",
        "date": date,
        "numdoc": numdoc,
        "valor": valor,
        "valor_tributavel": valor_tributavel,
        "iva": iva,
        "iva_dedutivel_per": "100%",
        "iva_dedutivel_valor": iva,
        "tipologia": tipologia,
        "iva_cativo_per": "0%",
        "iva_cativo_valor": "0,00",
        "linha": "1",
        "periodo": extract_periodo(date),
        "status": status,
        "descricao": descricao,
        "retencao": retencao,
        "retencao_valor": retencao_valor
    }

def extract_nif_empresa_sonangol(text: str) -> str:
    """Extrai NIF da Sonangol"""
    patterns = [
        r'Contribuinte\s*(\d{9})',
        r'NIF[:\s]*(\d{9})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return ""

def extract_nif_cliente_sonangol(text: str) -> str:
    """Extrai NIF do cliente na fatura da Sonangol"""
    patterns = [
        r'Contribuinte:\s*(\d{9})',
        r'Cliente:.*?Contribuinte:\s*(\d{9})',
        r'NIF.*?(\d{9})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""

def extract_numdoc_sonangol(text: str) -> str:
    """Extrai número do documento da Sonangol"""
    patterns = [
        r'(FR\s?\d+[/\-]\d+)',
        r'(FATURA RECIBO\s+[\w/\-]+)',
        r'FATURA RECIBO\s+([^\n]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def extract_date_sonangol(text: str) -> str:
    """Extrai data da fatura da Sonangol"""
    patterns = [
        r'Data:\s*(\d{2})[/\-](\d{2})[/\-](\d{4})',
        r'(\d{2})[/\-](\d{2})[/\-](\d{4})\s+\d{2}:\d{2}:\d{2}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            day, month, year = match.group(1), match.group(2), match.group(3)
            try:
                return f"{year}-{month}-{day}"
            except:
                continue
    return ""

def extract_valor_sonangol(text: str) -> str:
    """Extrai valor total da fatura da Sonangol"""
    patterns = [
        r'Total\s*\(Kwanza\)\s*([\d\s.,]+)',
        r'Total.*?([\d\s.,]+)\s*Kz',
        r'Total.*?([\d\s.,]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return format_value(match.group(1))
    return ""

def extract_nome_cliente_sonangol(text: str) -> str:
    """Extrai nome do cliente - pode estar vazio em faturas de combustível"""
    match = re.search(r'Cliente:\s*([^\n\r]+)', text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        if name != '-':
            return name
    return ""

def generate_gasoline_analysis(nome_empresa: str, nome_cliente: str, nif_cliente: str, valor: str, status: str) -> str:
    """Gera análise específica para faturas de combustível"""
    cliente_info = nome_cliente if nome_cliente else "identificado apenas por NIF"
    nif_info = nif_cliente if nif_cliente else "não identificado"
    
    status_text = "CUMPRE" if status == "CUMPRE" else "NÃO CUMPRE"
    
    return (f"Factura de combustível da {nome_empresa} para cliente {cliente_info} com NIF {nif_info}, "
            f"contendo valores totais de {valor} Kz. Descrição: abastecimento de combustível. "
            f"O documento contém IVA isento (0%) nos termos da legislação aplicável a combustíveis. "
            f"Não há retenção de IVA. A factura {status_text} requisitos legais.")

# Funções auxiliares mantidas da versão anterior
def split_invoice_blocks(text: str) -> List[str]:
    """Divide o texto em blocos individuais de faturas."""
    blocks = []
    
    patterns = [
        r'(RECIBO: RC BANK\d+/\d+.*?)(?=RECIBO: RC BANK\d+/\d+|$)',
        r'(FATURA RECIBO.*?)(?=FATURA RECIBO|$)',
        r'(Factura.*?Número: FTM?\s?\d+.*?)(?=Factura|$)',
        r'(FR\s?\d+[/\-]\d+.*?)(?=FR\s?\d+[/\-]\d+|$)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            blocks.extend(matches)
    
    if not blocks and len(text) > 200:
        chunks = re.split(r'\n\s*\n|\f', text)
        blocks = [chunk for chunk in chunks if is_likely_invoice(chunk)]
    
    return blocks if blocks else []

def is_likely_invoice(text: str) -> bool:
    """Verifica se o texto parece ser uma fatura"""
    invoice_indicators = [
        r'NIF:?\s?\d{9}',
        r'FTM?\s?\d+',
        r'FATURA',
        r'FACTURA',
        r'RECIBO',
        r'TOTAL.*?\d+[,\s]\d+'
    ]
    
    indicators_count = sum(1 for pattern in invoice_indicators if re.search(pattern, text, re.IGNORECASE))
    return indicators_count >= 2 and len(text.strip()) > 100

def parse_single_invoice(block: str, order: int) -> Dict[str, Any]:
    """Analisa um único bloco de fatura (para outros tipos)"""
    # Implementação simplificada para outros tipos de faturas
    nif_empresa = extract_nif_empresa(block)
    nif_cliente = extract_nif_cliente(block)
    numdoc = extract_numdoc(block)
    date = extract_date(block)
    valor = extract_valor(block)
    
    if not any([nif_empresa, nif_cliente, numdoc, date, valor]):
        return None
    
    status = determine_status(nif_empresa, nif_cliente, date, valor, numdoc)
    
    return {
        "analise": generate_analysis("", "", nif_cliente, valor, "0,00", "NÃO", "0,00", status, ""),
        "email": "",
        "regime": "Regime Geral",
        "nif_cliente": nif_cliente,
        "nif_empresa": nif_empresa,
        "num_ordem": str(order),
        "nome_cliente": "",
        "nome_empresa": "",
        "type_document": extract_type_document(numdoc),
        "date": date,
        "numdoc": numdoc,
        "valor": valor,
        "valor_tributavel": valor,
        "iva": "0,00",
        "iva_dedutivel_per": "100%",
        "iva_dedutivel_valor": "0,00",
        "tipologia": "",
        "iva_cativo_per": "0%",
        "iva_cativo_valor": "0,00",
        "linha": "1",
        "periodo": extract_periodo(date),
        "status": status,
        "descricao": "",
        "retencao": "NÃO",
        "retencao_valor": "0,00"
    }

def extract_nif_empresa(text: str) -> str:
    patterns = [
        r'Contribuinte\s*(\d{9})',
        r'NIF[:\s]*(\d{9})',
        r'NIF\s+Fornecedor[:\s]*(\d{9})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""

def extract_nif_cliente(text: str) -> str:
    patterns = [
        r'Cliente:.*?Contribuinte:\s*(\d{9})',
        r'NIF do Adquirente:\s*(\d{9})',
        r'Contribuinte:\s*(\d{9})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""

def extract_numdoc(text: str) -> str:
    patterns = [
        r'(FR\s?\d+[/\-]\d+)',
        r'(FTM?\s?\d+[/\-]\d+)',
        r'(RECIBO: RC BANK\d+/\d+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def extract_date(text: str) -> str:
    patterns = [
        r'Data:\s*(\d{2})[/\-](\d{2})[/\-](\d{4})',
        r'(\d{2})[/\-](\d{2})[/\-](\d{4})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            day, month, year = match.group(1), match.group(2), match.group(3)
            try:
                return f"{year}-{month}-{day}"
            except:
                continue
    return ""

def extract_valor(text: str) -> str:
    patterns = [
        r'Total.*?(\d+[,\s]\d+[,\s]\d+)',
        r'Valor.*?(\d+[,\s]\d+[,\s]\d+)',
        r'TOTAL.*?(\d+[,\s]\d+[,\s]\d+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return format_value(match.group(1))
    return ""

def extract_type_document(numdoc: str) -> str:
    if "FTM" in numdoc:
        return "FTM"
    elif "FR" in numdoc:
        return "FR"
    elif "FT" in numdoc:
        return "FT"
    elif "RC BANK" in numdoc:
        return "RC"
    return ""

def extract_periodo(date: str) -> str:
    if date and len(date) >= 7:
        return date[:7]
    return ""

def format_value(value_str: str) -> str:
    """Formata valores para o padrão 'XX XXX,XX'"""
    if not value_str:
        return ""
    
    clean_value = re.sub(r'[^\d,]', '', value_str)
    
    if ',' not in clean_value:
        clean_value = clean_value + ',00'
    
    parts = clean_value.split(',')
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else '00'
    decimal_part = decimal_part.ljust(2, '0')[:2]
    
    if len(integer_part) > 3:
        formatted_integer = ''
        for i, char in enumerate(reversed(integer_part)):
            if i > 0 and i % 3 == 0:
                formatted_integer = ' ' + formatted_integer
            formatted_integer = char + formatted_integer
    else:
        formatted_integer = integer_part
    
    return f"{formatted_integer},{decimal_part}"

def determine_status(nif_empresa: str, nif_cliente: str, date: str, valor: str, numdoc: str) -> str:
    required_fields = [nif_empresa, nif_cliente, date, valor, numdoc]
    if all(field for field in required_fields):
        return "CUMPRE"
    return "NÃO CUMPRE"

def generate_analysis(nome_empresa: str, nome_cliente: str, nif_cliente: str, 
                     valor: str, iva: str, retencao: str, retencao_valor: str, 
                     status: str, descricao: str) -> str:
    
    empresa_info = nome_empresa if nome_empresa else "desconhecido"
    cliente_info = nome_cliente if nome_cliente else "desconhecido"
    nif_info = nif_cliente if nif_cliente else "vazio"
    
    elements = []
    if valor: elements.append("números do documento")
    if valor: elements.append("valores totais")
    
    elements_text = ", ".join(elements) if elements else "dados básicos"
    
    status_text = "CUMPRE" if status == "CUMPRE" else "NÃO CUMPRE"
    
    return (f"Factura do fornecedor {empresa_info} para cliente {cliente_info} com NIF {nif_info}, "
            f"contendo {elements_text}. A factura {status_text} requisitos legais.")

def create_empty_invoice() -> Dict[str, Any]:
    return {
        "analise": "Factura do fornecedor desconhecido para cliente desconhecido com NIF vazio, contendo número do documento, datas, valores totais, IVA e retenção vazios. O documento não traz dados completos nem fiscalmente válidos. A factura NÃO CUMPRE requisitos legais.",
        "email": "",
        "regime": "Regime Geral",
        "nif_cliente": "",
        "nif_empresa": "",
        "num_ordem": "1",
        "nome_cliente": "",
        "nome_empresa": "",
        "type_document": "",
        "date": "",
        "numdoc": "",
        "valor": "",
        "valor_tributavel": "",
        "iva": "",
        "iva_dedutivel_per": "100%",
        "iva_dedutivel_valor": "",
        "tipologia": "",
        "iva_cativo_per": "0%",
        "iva_cativo_valor": "0,00",
        "linha": "1",
        "periodo": "",
        "status": "NÃO CUMPRE",
        "descricao": "",
        "retencao": "NÃO",
        "retencao_valor": ""
    }