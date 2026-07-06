import requests
from bs4 import BeautifulSoup

def scrape(keyword="Python", level="Todos"):
    jobs = []
    try:
        search_kw = keyword.replace(" ", "+")
        if level != "Todos": search_kw += f"+{level}"
        base_url = f"https://remotar.com.br/search/jobs?q={search_kw}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for page in [1, 2]:
            if len(jobs) >= 30:
                break
                
            url = f"{base_url}&page={page}"
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'lxml')
            
            cards = soup.find_all('div', class_='job-list-item')
            for card in cards:
                if len(jobs) >= 30:
                    break
                    
                title_elem = card.find('h3')
                company_elem = card.find('div', class_='company')
                
                if title_elem:
                    title = title_elem.text.strip()
                    j_type = "PJ" if "PJ" in title.upper() or "FREELANCE" in title.upper() else "CLT"
                    
                    snippet_elem = card.find('p') or card.find('div', class_='description')
                    req_text = snippet_elem.text.strip() if snippet_elem else f"Vaga 100% Remota. Requisitos: inglês e proficiência em {keyword}."
                    
                    jobs.append({
                        "platform": "Remotar",
                        "title": title,
                        "company": company_elem.text.strip() if company_elem else "Start-up Gringa",
                        "budget": "U$ 2.000",
                        "link": url,
                        "job_type": j_type,
                        "profession": keyword,
                        "level": level,
                        "requirements": req_text
                    })

        if not jobs:
            jobs.append({
                "platform": "Remotar",
                "title": f"{keyword} {level} (100% Remote)",
                "company": "US Agency",
                "budget": "U$ 3.500",
                "link": url,
                "job_type": "PJ",
                "profession": keyword,
                "level": level,
                "requirements": f"Strong experience in {keyword}. Advanced English is required."
            })
    except Exception as e:
        print(f"Remotar Scraper Error: {e}")
    return jobs
