import requests
from bs4 import BeautifulSoup
import urllib.parse

def scrape(keyword, level="Todos", country="Brasil"):
    jobs = []
    try:
        encoded_kw = urllib.parse.quote(keyword)
        url = f"https://www.99freelas.com.br/projects?q={encoded_kw}"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('li', class_='result-item')
            
            for item in items[:15]:
                title_el = item.find('h1', class_='title')
                if not title_el:
                    continue
                    
                title = title_el.text.strip()
                link_el = title_el.find('a')
                link = "https://www.99freelas.com.br" + link_el['href'] if link_el else url
                
                desc_el = item.find('div', class_='description')
                desc = desc_el.text.strip() if desc_el else "Sem descrição"
                
                jobs.append({
                    "platform": "99Freelas",
                    "title": title,
                    "company": "Cliente 99Freelas",
                    "budget": "PJ - A Combinar",
                    "link": link,
                    "job_type": "Freelance / PJ",
                    "profession": keyword,
                    "level": level,
                    "requirements": desc[:250] + "..." if len(desc) > 250 else desc
                })
    except Exception as e:
        print("Erro 99Freelas:", e)
        
    return jobs
