"""
Motor de Auto-Apply: Preenche formulários simples de candidatura 
usando os dados do currículo do usuário.

Estratégia:
- Para vagas Gupy: Usa a API de candidatura da Gupy (POST)
- Para vagas com Easy Apply (LinkedIn): Abre o link direto
- Para vagas genéricas: Envia e-mail com currículo anexado (se houver e-mail na vaga)
- Fallback: Retorna o link direto para aplicação manual
"""

import os
import re
import requests
from loguru import logger


def extract_email_from_text(text: str) -> str:
    """Extrai o primeiro e-mail encontrado no texto da vaga."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def prepare_candidate_data(curriculo_path: str = "curriculo.txt") -> dict:
    """Lê o currículo e extrai dados básicos do candidato para preenchimento de formulários."""
    data = {
        "name": "",
        "email": "",
        "phone": "",
        "resume_text": "",
        "resume_pdf_path": "temp_curriculo.pdf"
    }
    
    if os.path.exists(curriculo_path):
        with open(curriculo_path, "r", encoding="utf-8") as f:
            text = f.read()
            data["resume_text"] = text
            
            # Extrair e-mail do candidato
            email = extract_email_from_text(text)
            if email:
                data["email"] = email
                
            # Extrair telefone (formato BR)
            phone_pattern = r'(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}[-\s]?\d{4}'
            phone_match = re.search(phone_pattern, text)
            if phone_match:
                data["phone"] = phone_match.group(0)
                
            # Extrair nome (primeira linha não vazia que não parece ser um cargo)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                first_line = lines[0]
                # Se a primeira linha não contém @ ou números longos, provavelmente é o nome
                if '@' not in first_line and not re.search(r'\d{5,}', first_line):
                    data["name"] = first_line
    
    return data


def apply_via_gupy(job_url: str, candidate: dict) -> dict:
    """
    Tenta aplicar para uma vaga da Gupy usando a API pública.
    Nota: A Gupy exige OAuth para candidatura completa, então este método
    retorna o link direto para candidatura rápida.
    """
    try:
        # A Gupy não permite candidatura 100% via API sem OAuth do candidato.
        # Retornamos o link direto de candidatura.
        return {
            "success": False,
            "method": "gupy_redirect",
            "message": "Gupy exige login do candidato. Link direto gerado.",
            "apply_url": job_url
        }
    except Exception as e:
        logger.error(f"Erro ao aplicar via Gupy: {e}")
        return {"success": False, "method": "error", "message": str(e)}


def apply_via_email(job: dict, candidate: dict) -> dict:
    """
    Verifica se a vaga contém um e-mail de contato e prepara o envio.
    """
    job_text = job.get("requirements", "") + " " + job.get("title", "")
    contact_email = extract_email_from_text(job_text)
    
    if not contact_email:
        return {
            "success": False,
            "method": "no_email",
            "message": "Nenhum e-mail de contato encontrado na vaga."
        }
    
    # Preparar dados do e-mail (o envio real será feito via Gmail API já integrada)
    return {
        "success": True,
        "method": "email",
        "message": f"E-mail de candidatura preparado para: {contact_email}",
        "contact_email": contact_email,
        "subject": f"Candidatura: {job.get('title', 'Vaga')} - {candidate.get('name', 'Candidato')}",
        "body": f"""Prezados,

Meu nome é {candidate.get('name', 'Candidato')} e venho por meio deste me candidatar à vaga de {job.get('title', 'a vaga anunciada')}.

Segue meu currículo em anexo para análise.

Atenciosamente,
{candidate.get('name', 'Candidato')}
{candidate.get('email', '')}
{candidate.get('phone', '')}
""",
        "attachment": candidate.get("resume_pdf_path", "")
    }


def auto_apply(job: dict) -> dict:
    """
    Motor principal de Auto-Apply. Decide a melhor estratégia de candidatura
    baseada na plataforma de origem da vaga.
    """
    candidate = prepare_candidate_data()
    platform = job.get("platform", "").lower()
    link = job.get("link", "")
    
    result = {
        "success": False,
        "method": "manual",
        "message": "Aplique manualmente clicando no link da vaga.",
        "apply_url": link
    }
    
    try:
        # Estratégia por plataforma
        if "gupy" in platform:
            result = apply_via_gupy(link, candidate)
            
        elif "linkedin" in platform:
            # LinkedIn Easy Apply requer autenticação OAuth
            result = {
                "success": False,
                "method": "linkedin_redirect",
                "message": "LinkedIn Easy Apply requer login. Link direto gerado.",
                "apply_url": link
            }
            
        else:
            # Tenta encontrar e-mail de contato na vaga
            email_result = apply_via_email(job, candidate)
            if email_result["success"]:
                result = email_result
            else:
                result["apply_url"] = link
                
    except Exception as e:
        logger.error(f"Erro no Auto-Apply: {e}")
        result["message"] = f"Erro: {e}"
    
    return result
