import requests
import re

def scrape(keyword, level="Todos", country="Brasil"):
    # Se o usuário quer vagas fora do Brasil, pulamos.
    if country != "Brasil" and country != "Brasil (Remoto)":
        return []

    base_url = "https://trampos.co/api/v2/opportunities"
    page = 1
    jobs = []

    try:
        while page <= 2: # Limitamos a 2 páginas para não estourar tempo
            response = requests.get(base_url, params={'page': page})
            if response.status_code != 200:
                break
                
            data = response.json()
            opportunities = data.get('opportunities', [])
            
            if not opportunities:
                break
                
            for job in opportunities:
                title = job.get('name', '')
                
                # Filtrar superficialmente pela keyword
                if keyword.lower() not in title.lower():
                    continue

                company_data = job.get('company', {})
                company_name = company_data.get('name', 'Confidencial') if company_data else 'Confidencial'
                
                salary = job.get('salary') or "A Combinar"
                location_city = job.get('city', '')
                location_state = job.get('state', '')
                location = f"{location_city} - {location_state}" if location_city else "Não informado"
                
                desc = job.get('description', '')
                desc_clean = re.sub('<[^<]+>', '', desc).replace('\n', ' ') if desc else "Sem descrição detalhada."
                
                j_type = "PJ" if "PJ" in title.upper() else "CLT"
                
                job_info = {
                    "platform": "Trampos.co",
                    "title": title,
                    "company": company_name,
                    "budget": salary,
                    "link": f"https://trampos.co/oportunidades/{job.get('id')}",
                    "job_type": j_type,
                    "profession": keyword,
                    "level": level,
                    "requirements": desc_clean[:1200]
                }
                jobs.append(job_info)
                
            page += 1
            
    except Exception as e:
        print(f"Erro Trampos.co: {e}")
        
    return jobs
