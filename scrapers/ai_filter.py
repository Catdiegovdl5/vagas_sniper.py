import json
from loguru import logger
import asyncio
import random
from groq import AsyncGroq
from pydantic import BaseModel, Field

# O arsenal de chaves que o usuário nos forneceu para triplicar a cota (18.000 Tokens/min)
import os
API_KEYS = [
    os.environ.get("GROQ_API_KEY_1", ""),
    os.environ.get("GROQ_API_KEY_2", ""),
    os.environ.get("GROQ_API_KEY_3", "")
]

# Semáforo para garantir que no máximo 4 requisições batam no Groq simultaneamente
sem = asyncio.Semaphore(4)

class JobEvaluation(BaseModel):
    aprovado: bool = Field(description="True se a vaga atende aos critérios obrigatórios. False se violar as regras de reprovação imediata.")
    is_freelance: bool = Field(description="True se a vaga for projeto pontual, freelancer ou remunerada por hora.")
    vaga_corresponde_ao_cargo: bool
    localidade_correta: bool
    exige_experiencia: bool
    exige_faculdade: bool = Field(description="True se a vaga exigir ensino superior obrigatório (completo ou cursando).")
    salary_declared: bool = Field(description="True se a vaga exibe um valor de salário/remuneração real (ex: R$ 2.000, R$ 3.500). False se disser 'A combinar' ou não informar.")
    has_benefits: bool = Field(description="True se a vaga listar benefícios concretos como VR, VA, VT, plano de saúde. False se não mencionar.")
    score: int
    justificativa_curta: str
    reqs: str
    bonus: str
    benefits: str
    model: str
    proposal: str = Field(description="Se a vaga for freelancer e aprovada, escreva uma proposta longa e detalhada.")

async def score_job_match(resume_text: str, job: dict, target_keyword: str = None, target_location: str = None, target_level: str = "Todos", target_education: str = "Todos", target_contract: str = "Todos") -> dict:
    if not resume_text or len(resume_text) < 10:
        return {
            "aprovado": True,
            "score": 100,
            "reason": "Nenhum currículo configurado. Vaga aprovada.",
            "reqs": "",
            "bonus": "",
            "benefits": "",
            "model": "",
            "salary_declared": False,
            "has_benefits": False,
            "exige_faculdade": False,
            "is_freelance": False,
            "vaga_corresponde_ao_cargo": True,
            "localidade_correta": True,
            "exige_experiencia": False
        }

    # Limite aumentado para garantir que a IA leia requisitos que aparecem no meio/fim da descrição
    req_trunc = job.get('requirements', '')[:2500]
    resume_trunc = resume_text[:2500]

    prompt = f"""
Você é um validador de dados binário e impiedoso. Sua função é avaliar a vaga abaixo com base nos critérios do candidato.

Regras de Reprovação Imediata:
1. O candidato busca o cargo "{target_keyword}". Se a vaga for da mesma área (ex: "Auxiliar", "Analista", "Especialista" de Marketing quando pediu "Assistente de Marketing") ou um sinônimo, APROVE. Só REPROVE (vaga_corresponde_ao_cargo=false, aprovado=false) se a vaga for de uma área COMPLETAMENTE diferente (ex: TI quando pediu Vendas, ou Enfermagem quando pediu Marketing).
2. Localidade: "{target_location}". SEJA EXTREMAMENTE RÍGIDO: Se o candidato quiser "Brasil (Remoto)", REPROVE OBRIGATORIAMENTE qualquer vaga que cite ser Híbrida ou Presencial, sem nenhuma exceção. Se o candidato quiser uma cidade específica, reprove vagas em cidades diferentes. Em caso de reprovação, defina localidade_correta=false e aprovado=false.
3. Nível do candidato: "{target_level}". Se o nível for "Júnior" e a vaga exigir "Experiência comprovada", "Pleno", "Sênior", ou +1 ano de experiência, REPROVE (exige_experiencia=true, aprovado=false).
4. Se o usuário estiver no Brasil e a vaga citar salários em Dólar/Euro ($/€) ou exigir "Inglês Fluente" (sendo o candidato nível Júnior), REPROVE.
5. Se a descrição for um snippet cortado com reticências (ex: "Our sales team is growing quickly..."), NÃO invente os requisitos. Escreva "Resumo curto fornecido pela plataforma" nos campos reqs e benefits.
6. Modalidade do candidato: "{target_contract}". Avalie a modalidade da vaga. Se for projeto temporário/freela, defina is_freelance=true, senão false. SEJA RÍGIDO NA APROVAÇÃO: Se o candidato pedir "CLT", REPROVE vagas "PJ" ou "Freelancer". Se pedir "PJ", REPROVE vagas "CLT" ou "Freelancer". Se pedir "Freelancer", REPROVE vagas fixas (CLT ou PJ). Se for "Todos", não reprove por modalidade. Em caso de reprovação, aprovado=false.
7. Formação do candidato: "{target_education}". SEJA IMPIEDOSO: Se a formação do candidato for "Sem Formação", REPROVE IMEDIATAMENTE qualquer vaga que cite Ensino Superior, Faculdade, Graduação, Bacharelado ou Cursando como requisito OBRIGATÓRIO. Só aprove se a faculdade for tratada como "Diferencial", "Desejável" ou não for mencionada. Se a formação for "Todos", não reprove por educação. Em caso de reprovação, defina exige_faculdade=true e aprovado=false.
8. Regra de Ouro IA: Se a busca ({target_keyword}) for relacionada a Inteligência Artificial (ex: "Especialista em IA", "AI Coder", "Engenheiro de Prompt", "Consultor de IA"), a vaga DEVE ser OBRIGATORIAMENTE técnica (Desenvolvimento, Engenharia de Dados, Python, LLMs, Machine Learning). REPROVE SUMARIAMENTE vagas de Marketing de Performance (Google Ads, Meta Ads), Criação de Conteúdo genérica ou Automação Básica de WhatsApp (ManyChat, Chatbots de atendimento), a menos que o termo de busca peça exatamente isso. Em caso de dúvida sobre a vaga ser apenas uma ferramenta de marketing em vez de IA real, REPROVE (vaga_corresponde_ao_cargo=false, aprovado=false).

Organize a resposta ESTRITAMENTE em JSON que satisfaça o seguinte schema (todos os campos obrigatórios):
- "aprovado" (bool)
- "is_freelance" (bool)
- "vaga_corresponde_ao_cargo" (bool)
- "localidade_correta" (bool)
- "exige_experiencia" (bool)
- "exige_faculdade" (bool)
- "score": (int de 0 a 100) Compatibilidade com o currículo e com o termo {target_keyword}. Baseie o score apenas na relevância do cargo e requisitos com o perfil do candidato.
- "salary_declared": (bool) True se a vaga exibe um valor de salário real. False se não informar.
- "has_benefits": (bool) True se a vaga listar benefícios concretos (VR, VA, VT, plano de saúde). False se não mencionar.
- "justificativa_curta": (string) 1 frase curta explicando se passou ou a regra exata que violou.
- "reqs": (string) Requisitos Obrigatórios REAIS da vaga. Procure por seções com títulos como "Requisitos", "Esperamos que você possua", "O que buscamos", "Pré-requisitos", "Perfil desejado". IGNORE parágrafos de cultura, valores, missão da empresa ou descrição genérica do cargo. Se não encontrar, escreva "Não informado".
- "bonus": (string) Diferenciais/Desejaveis. Procure por seções como "Diferenciais", "Será um diferencial", "Desejável", "Nice to have". Se não encontrar, escreva "Não mencionado".
- "benefits": (string) Salário e Benefícios. Procure por seções como "Benefícios", "O que oferecemos", "Remuneração". Liste todos os benefícios encontrados (VR, VA, VT, plano de saúde, auxílio creche, etc.). Se não encontrar, escreva "Não informado".
- "model": (string) Modelo de Trabalho e Cidade (Remoto, Presencial, Híbrido + cidade se mencionar).
- "proposal": (string) RETORNE UMA ÚNICA STRING CONTÍNUA (TEXTO PLANO). NÃO RETORNE UM OBJETO JSON! SE a vaga for APROVADA E a Plataforma for Workana, 99Freelas ou Freelancer, crie uma Proposta Comercial HÍBRIDA (em Português do Brasil) com limite estrito de 1500 caracteres. Siga EXATAMENTE esta estrutura:
  1. Abertura Humana e Conversacional: "Oi! Vi seu projeto sobre [Tema] e percebi que o seu principal desafio hoje é [Gargalo real]". Fale de forma empática e próxima, como se estivesse conversando com o cliente no WhatsApp.
  2. Plano S-Tier (Tabela Markdown OBRIGATÓRIA): Mostre sua autoridade técnica. Diga "Para resolver isso rápido, montei esse plano de execução:" e crie uma tabela (FASE | ARQUITETURA | IMPACTO) com 3 etapas práticas usando suas habilidades do currículo (GTM, Meta CAPI, Python, Automação, etc).
  3. Autoridade e Orçamento: Fale brevemente (1 frase) sobre sua experiência/certificações que garantem o resultado. Opcionalmente, ancore opções de investimento se fizer sentido.
  4. Xeque-Mate (CTA Amigável): Finalize com UMA PERGUNTA TÉCNICA E ESPECÍFICA sobre o projeto para puxar assunto, seguida de um convite caloroso: "Vamos bater um papo rápido sobre isso? Confira meu portfólio e cases de sucesso aqui: https://linktr.ee/diegogrowth". Assine como "Abraço, Diego - Growth Engineer".
  Se a vaga for REPROVADA ou se a Plataforma NÃO for de freelancer (ex: LinkedIn, Gupy, Infojobs), escreva apenas "N/A".

--- CURRÍCULO ---
{resume_trunc}
--- VAGA ---
Título: {job.get('title', '')}
Plataforma: {job.get('platform', 'Desconhecida')}
Info: {job.get('budget', '')} | {job.get('job_type', '')}
Desc: {req_trunc}
"""

    async with sem:
        for tentativa in range(4):
            key = random.choice(API_KEYS)
            client = AsyncGroq(api_key=key)
            
            try:
                response = await client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct", 
                    messages=[
                        {"role": "system", "content": "Você é um validador impiedoso que responde APENAS em JSON seguindo exatamente os booleanos e as chaves exigidas."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={ "type": "json_object" }
                )
                
                result_text = response.choices[0].message.content
                result_json = json.loads(result_text)
                
                # Validação estrita via Pydantic
                eval_obj = JobEvaluation(**result_json)
                
                aprovado = eval_obj.aprovado
                score = eval_obj.score
                reason = eval_obj.justificativa_curta

                if aprovado:
                    violated = []
                    if eval_obj.vaga_corresponde_ao_cargo == False:
                        violated.append("vaga_corresponde_ao_cargo == False")
                    if eval_obj.is_freelance == True and target_contract not in ["Freelancer", "Todos"]:
                        violated.append("is_freelance == True (candidato quer fixo)")
                    if eval_obj.localidade_correta == False:
                        violated.append("localidade_correta == False")
                    if eval_obj.exige_faculdade == True and target_education == "Sem Formação":
                        violated.append("exige_faculdade == True")
                    if eval_obj.exige_experiencia == True and target_level == "Júnior":
                        violated.append("exige_experiencia == True")
                    
                    if target_level == "Júnior":
                        import re
                        title_raw = job.get('title', '') or ''
                        budget_raw = job.get('budget', '') or ''
                        reqs_raw = job.get('requirements', '') or ''
                        
                        texts_to_check = [title_raw, budget_raw, reqs_raw]
                        
                        # Check foreign currency
                        has_foreign_currency = False
                        for text in texts_to_check:
                            text_lower = text.lower()
                            if "€" in text or any(kw in text_lower for kw in ["usd", "euro", "euros", "dollar", "dollars"]) or re.search(r'(?<![Rr])\$', text):
                                has_foreign_currency = True
                                break
                        if has_foreign_currency:
                            violated.append("foreign_currency_detected")
                            
                        # Check fluent English
                        has_fluent_english = False
                        fluent_english_kws = ["inglês fluente", "ingles fluente", "fluent english", "fluency in english", "english fluent", "english: fluent", "ingles: fluente", "inglês: fluente"]
                        for text in texts_to_check:
                            text_lower = text.lower()
                            if any(kw in text_lower for kw in fluent_english_kws):
                                has_fluent_english = True
                                break
                        if has_fluent_english:
                            violated.append("fluent_english_detected")
                    
                    if violated:
                        aprovado = False
                        score = 0
                        reason = f"[Hard-Lock Override] Violated conditions: {', '.join(violated)}"

                return {
                    "aprovado": aprovado,
                    "score": score,
                    "reason": reason,
                    "reqs": eval_obj.reqs,
                    "bonus": eval_obj.bonus,
                    "benefits": eval_obj.benefits,
                    "model": eval_obj.model,
                    "salary_declared": eval_obj.salary_declared,
                    "has_benefits": eval_obj.has_benefits,
                    "exige_faculdade": eval_obj.exige_faculdade,
                    "is_freelance": eval_obj.is_freelance,
                    "vaga_corresponde_ao_cargo": eval_obj.vaga_corresponde_ao_cargo,
                    "localidade_correta": eval_obj.localidade_correta,
                    "exige_experiencia": eval_obj.exige_experiencia,
                    "proposal": getattr(eval_obj, 'proposal', '')
                }
                
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "rate limit" in err_msg:
                    await asyncio.sleep(2 + tentativa)
                else:
                    logger.error(f"Erro ao extrair JSON: {e}")
                    return {
                        "aprovado": False,
                        "score": 0,
                        "reason": "Erro no modelo estruturado.",
                        "reqs": "",
                        "bonus": "",
                        "benefits": "",
                        "model": "",
                        "salary_declared": False,
                        "has_benefits": False,
                        "exige_faculdade": False,
                        "is_freelance": False,
                        "vaga_corresponde_ao_cargo": True,
                        "localidade_correta": True,
                        "exige_experiencia": False
                    }
                    
        return {
            "aprovado": False,
            "score": 0,
            "reason": "Timeout da IA.",
            "reqs": "",
            "bonus": "",
            "benefits": "",
            "model": "",
            "salary_declared": False,
            "has_benefits": False,
            "exige_faculdade": False,
            "is_freelance": False,
            "vaga_corresponde_ao_cargo": True,
            "localidade_correta": True,
            "exige_experiencia": False
        }

async def analyze_resume_for_keywords(resume_text: str) -> list:
    if not resume_text or len(resume_text) < 20:
        return ["Gestor de Tráfego", "Python Scraping", "Analista de Dados"]

    prompt = f"""
Você é um estrategista de carreira sênior. 
Leia o currículo do candidato e sugira os 3 melhores termos de busca exatos (títulos de cargos) para encontrar vagas em plataformas como LinkedIn e Indeed que combinem perfeitamente com ele.
Seja preciso e use os títulos mais valorizados pelo mercado B2B ou remoto atual.

Retorne APENAS um objeto JSON com a chave "keywords" contendo um array de 3 strings (ex: {{"keywords": ["Engenheiro de Dados", "Desenvolvedor Python", "Automação"]}}).

--- CURRÍCULO ---
{resume_text[:2000]}
"""

    async with sem:
        for tentativa in range(3):
            key = random.choice(API_KEYS)
            client = AsyncGroq(api_key=key)
            
            try:
                response = await client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct", 
                    messages=[
                        {"role": "system", "content": "Responda ESTRITAMENTE em formato JSON contendo a chave 'keywords' com 3 strings."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={ "type": "json_object" }
                )
                
                result_text = response.choices[0].message.content
                result_json = json.loads(result_text)
                
                return result_json.get("keywords", ["SDR", "Growth", "Automação"])[:3]
                
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "rate limit" in err_msg:
                    await asyncio.sleep(2 + tentativa)
                else:
                    logger.error(f"Erro ao gerar keywords: {e}")
                    return ["Gestor de Tráfego", "Python", "Analista"]
                    
        return ["Freelancer", "Dev", "Marketing"]

async def extract_hunt_intent(message_text: str) -> dict:
    if not message_text or len(message_text) < 3:
        return {"keyword": "Vagas", "location": "Brasil (Remoto)"}

    prompt = f"""
Você é um bot assistente de busca de empregos. 
O usuário enviou a seguinte mensagem de texto livre: "{message_text}"

Extraia os seguintes filtros de acordo com o contexto:
1. "keyword": A profissão principal (ex: "vendedor", "desenvolvedor").
2. "location": A localidade. Escolha ESTRITAMENTE entre: "Londrina/PR", "Assaí/PR" ou "Brasil (Remoto)".
3. "level": O nível de experiência. Escolha ESTRITAMENTE entre: "Todos", "Júnior", "Pleno" ou "Sênior". Se o texto disser "sem experiência", "estágio", "primeiro emprego" ou "iniciante", escolha "Júnior".
4. "contract": O tipo de contrato. Escolha ESTRITAMENTE entre: "Todos", "CLT" ou "PJ".
5. "education": O nível de formação exigido. Escolha ESTRITAMENTE entre: "Todos" ou "Sem Formação". Se o texto pedir "sem faculdade", "sem diploma", "sem escolaridade", escolha "Sem Formação".

Retorne APENAS um objeto JSON válido contendo essas 5 chaves.
Exemplo: {{"keyword": "vendedor", "location": "Londrina/PR", "level": "Júnior", "contract": "Todos", "education": "Todos"}}
"""

    async with sem:
        for tentativa in range(3):
            key = random.choice(API_KEYS)
            client = AsyncGroq(api_key=key)
            try:
                response = await client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct", 
                    messages=[
                        {"role": "system", "content": "Você é um extrator de intenções JSON estrito."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={ "type": "json_object" }
                )
                
                result_text = response.choices[0].message.content
                result_json = json.loads(result_text)
                
                return {
                    "keyword": result_json.get("keyword", "Vagas"),
                    "location": result_json.get("location", "Brasil (Remoto)"),
                    "level": result_json.get("level", "Todos"),
                    "contract": result_json.get("contract", "Todos"),
                    "education": result_json.get("education", "Todos")
                }
                
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "rate limit" in err_msg:
                    await asyncio.sleep(2 + tentativa)
                else:
                    logger.error(f"Erro ao extrair intenção: {e}")
                    return {"keyword": "Vagas", "location": "Brasil (Remoto)"}
                    
        return {"keyword": "Vagas", "location": "Brasil (Remoto)"}
