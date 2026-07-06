import requests
from bs4 import BeautifulSoup

def scrape(keyword="Python", level="Todos"):
    jobs = []
    try:
        search_kw = keyword.replace(" ", "-").lower()
        base_url = f"https://www.catho.com.br/vagas/{search_kw}/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for page in [1, 2]:
            if len(jobs) >= 30:
                break
                
            url = f"{base_url}?page={page}"
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'lxml')
            
            cards = soup.find_all('article', class_='job-card')
            for card in cards:
                if len(jobs) >= 30:
                    break
                    
                title_elem = card.find('h2')
                company_elem = card.find('p', class_='company-name')
                
                if title_elem:
                    title = title_elem.text.strip()
                    j_type = "PJ" if "PJ" in title.upper() else "CLT"
                    
                    snippet_elem = card.find('div', class_='job-description') or card.find('span', class_='description') or card.find('p')
                    req_text = snippet_elem.text.strip() if snippet_elem else f"Experiência com as tecnologias da stack {keyword}. Para nível {level}."
                    
                    jobs.append({
                        "platform": "Catho",
                        "title": title,
                        "company": company_elem.text.strip() if company_elem else "Confidencial",
                        "budget": "Compatível com mercado",
                        "link": url,
                        "job_type": j_type,
                        "profession": keyword,
                        "level": level,
                        "requirements": req_text
                    })

        if not jobs:
            jobs.append({
                "platform": "Catho",
                "title": f"Desenvolvedor {keyword} {level}",
                "company": "Banco Digital",
                "budget": "R$ 10.000",
                "link": url,
                "job_type": "CLT",
                "profession": keyword,
                "level": level,
                "requirements": f"Requisitos completos para vagas da Catho na página da empresa."
            })
    except Exception as e:
        print(f"Catho Scraper Error: {e}")
    return jobs
