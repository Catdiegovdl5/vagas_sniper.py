import requests
import re

def scrape(keyword, level="Todos", country="Brasil"):
    # A Gupy atua quase integralmente no Brasil, mas se o usuário focar em Gupy, é corporativo.
    if country != "Brasil" and country != "Brasil (Remoto)":
        return []

    jobs = []
    base_url = "https://employability-portal.gupy.io/api/v1/jobs"
    
    # A Gupy geralmente não suporta filtros complexos via URL como 'Júnior' etc, 
    # então usamos apenas a keyword principal para maximizar resultados.
    search_term = keyword
    
    limit = 30
    offset = 0
    
    try:
        response = requests.get(base_url, params={'jobName': search_term, 'limit': limit, 'offset': offset})
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])
            
            for item in items:
                title = item.get('name', 'Sem título')
                company = item.get('careerPageName', 'Confidencial')
                
                # A Gupy tem o link amigável da vaga
                link = item.get('jobUrl', '#')
                
                # A API retorna alguns dados uteis:
                job_type = item.get('type', 'CLT') 
                workplace = item.get('workplaceType', 'Presencial')
                
                # A descrição vem num campo 'description', vamos extrair se houver
                desc = item.get('description', '')
                desc_clean = re.sub('<[^<]+>', '', desc).replace('\n', ' ') if desc else "Acesse o link da Gupy para ver os detalhes."
                
                # Se for nível "Júnior", podemos pular se o título disser Pleno/Sênior explicitamente, economizando tokens.
                if level.lower() == "júnior" or level.lower() == "sem experiência":
                    if "pleno" in title.lower() or "senior" in title.lower() or "sênior" in title.lower():
                        continue
                        
                job_info = {
                    "platform": "Gupy",
                    "title": title,
                    "company": company,
                    "budget": "A Combinar",
                    "link": link,
                    "job_type": job_type,
                    "profession": keyword,
                    "level": level,
                    "requirements": f"[{workplace}] {desc_clean[:1200]}"
                }
                jobs.append(job_info)
                
    except Exception as e:
        print(f"Erro Gupy: {e}")
        
    return jobs
