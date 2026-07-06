import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

try:
    from curl_cffi import requests as requests_cffi
except ImportError:
    requests_cffi = None

def scrape(keyword, level="Todos", country="Brasil"):
    jobs = []
    try:
        search_kw = f"{keyword}"
        if level != "Todos":
            search_kw += f" {level}"
            
        base_url = "jooble.org"
        loc = ""
        if country == "Brasil": 
            base_url = "br.jooble.org"
            loc = "Brazil"
        elif country == "USA": 
            loc = "United States"
        elif "Londrina" in country:
            base_url = "br.jooble.org"
            loc = "Londrina"
        elif "Assaí" in country:
            base_url = "br.jooble.org"
            loc = "Assaí"
            
        url = f"https://{base_url}/api/0031603e-bd0a-4505-ad10-383c420d804f"
        
        payload = {
            "keywords": search_kw,
            "location": loc,
            "page": "1"
        }
        
        headers = {
            "Content-type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        if data.get("jobs"):
            for item in data["jobs"][:30]:
                title = item.get("title", "Sem título")
                j_type = "PJ" if "PJ" in title.upper() else "CLT"
                
                link = item.get("link", "#")
                description = ""
                final_url = link
                
                if link and link != "#":
                    try:
                        redirect_headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
                        }
                        
                        if requests_cffi:
                            r = requests_cffi.get(link, headers=redirect_headers, allow_redirects=True, timeout=12, impersonate="chrome110")
                        else:
                            r = requests.get(link, headers=redirect_headers, allow_redirects=True, timeout=12)
                            
                        final_url = r.url
                        html_content = r.text
                        
                        if r.status_code == 200:
                            soup = BeautifulSoup(html_content, "html.parser")
                            
                            if "gupy.io" in final_url:
                                desc_el = (soup.find(attrs={"data-testid": "vacancy-description-text"}) or 
                                           soup.find(attrs={"data-testid": "text-description"}) or
                                           soup.find(class_=re.compile(r"description|vacancy", re.I)))
                            elif "indeed.com" in final_url:
                                desc_el = soup.find(id="jobDescriptionText")
                            elif "jooble" in final_url:
                                desc_el = (soup.find("div", class_="job-description_description") or 
                                           soup.find("div", class_="description") or
                                           soup.find(class_=re.compile(r"description|desc", re.I)))
                            else:
                                desc_el = (soup.find(id="jobDescriptionText") or 
                                           soup.find("div", class_=re.compile(r"description|jobDescription|job-desc|vaga-desc|vacancy-desc", re.I)) or
                                           soup.find(attrs={"data-testid": re.compile(r"description|vacancy", re.I)}) or
                                           soup.find("article") or
                                           soup.find("main"))
                                           
                            if desc_el:
                                description = desc_el.get_text(separator="\n").strip()
                    except Exception as redirect_e:
                        print(f"Error following redirect for Jooble job {link}: {redirect_e}")
                
                if not description or len(description) < 150:
                    api_snippet = item.get("snippet", "")
                    description = api_snippet.replace('<b>', '').replace('</b>', '').replace('\n', ' ').strip()
                    
                jobs.append({
                    "platform": "Jooble",
                    "title": title,
                    "company": item.get("company", "Confidencial"),
                    "budget": item.get("salary") or "A Combinar",
                    "link": final_url,
                    "job_type": j_type,
                    "profession": keyword,
                    "level": level,
                    "requirements": description
                })
    except Exception as e:
        print("Erro Jooble:", e)
        
    if not jobs:
        jobs.append({
            "platform": "Jooble",
            "title": f"Sem vagas API Jooble para {keyword} ({level})",
            "company": "N/A",
            "budget": "N/A",
            "link": "#",
            "job_type": "N/A",
            "profession": keyword,
            "level": level,
            "requirements": "Não houve resultados."
        })
    return jobs
