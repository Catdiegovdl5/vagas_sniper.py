from curl_cffi import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import re

def scrape(keyword, level="Todos", country="Brasil"):
    if "Londrina" in country:
        loc_param = "Londrina%2C%20Paran%C3%A1%2C%20Brasil"
    elif "Assaí" in country:
        loc_param = "Assa%C3%AD%2C%20Paran%C3%A1%2C%20Brasil"
    else:
        loc_param = "Brasil"
        
    jobs = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    encoded_kw = urllib.parse.quote(keyword)
    
    # Return at least 10 valid jobs. Increment start offset (0, 25, 50, 75, 100, 125, etc.)
    offsets = [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250]
    
    for start in offsets:
        if len(jobs) >= 10:
            break
            
        url = f"https://br.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_kw}&location={loc_param}&start={start}"
        try:
            response = requests.get(url, impersonate="chrome110", headers=headers, timeout=15)
            if response.status_code != 200:
                time.sleep(2)
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.find_all("li")
            if not cards:
                break
                
            for card in cards:
                if len(jobs) >= 10:
                    break
                    
                title_el = card.find("h3", class_="base-search-card__title")
                title = title_el.text.strip() if title_el else "Sem Título"
                
                comp_el = card.find("h4", class_="base-search-card__subtitle")
                company = comp_el.text.strip() if comp_el else "Empresa Confidencial"
                
                link_el = card.find("a", class_="base-card__full-link")
                link = link_el.get("href", "") if link_el else ""
                
                if link and "?" in link:
                    link = link.split("?")[0]
                    
                loc_el = card.find("span", class_="job-search-card__location")
                location = loc_el.text.strip() if loc_el else "Remoto/Brasil"
                
                if title == "Sem Título" or not link:
                    continue
                    
                # Extract job_id
                job_id = None
                
                # Check data-entity-urn
                div_card = card.find(attrs={"data-entity-urn": True})
                if div_card:
                    urn = div_card["data-entity-urn"]
                    if "jobPosting:" in urn:
                        job_id = urn.split("jobPosting:")[-1].strip()
                
                if not job_id and card.has_attr("data-entity-urn"):
                    urn = card["data-entity-urn"]
                    if "jobPosting:" in urn:
                        job_id = urn.split("jobPosting:")[-1].strip()
                        
                # Extract from link URL
                if not job_id and link:
                    match = re.search(r'/view/(?:.+?-)?(\d+)', link)
                    if match:
                        job_id = match.group(1)
                    else:
                        match_fallback = re.search(r'\b\d{8,12}\b', link)
                        if match_fallback:
                            job_id = match_fallback.group(0)
                            
                if not job_id:
                    continue
                    
                # Fetch full description using guest API
                desc_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
                description_text = ""
                is_full_time = False
                
                try:
                    desc_response = requests.get(desc_url, headers=headers, impersonate="chrome110", timeout=15)
                    if desc_response.status_code == 200:
                        desc_soup = BeautifulSoup(desc_response.text, "html.parser")
                        
                        desc_container = desc_soup.find(class_="show-more-less-html__markup") or desc_soup.find(class_="description__text") or desc_soup.find(class_="jobs-description")
                        if not desc_container:
                            desc_container = desc_soup
                        
                        description_text = desc_container.get_text(separator="\n").strip()
                        
                        # Filter for full-time jobs only
                        criteria_items = desc_soup.find_all(class_=re.compile(r"job-criteria|criteria-text"))
                        for item in criteria_items:
                            text = item.get_text().strip().lower()
                            if "tempo integral" in text or "full-time" in text or "full time" in text:
                                is_full_time = True
                                break
                                
                        if not is_full_time:
                            desc_lower = description_text.lower()
                            if "tempo integral" in desc_lower or "full-time" in desc_lower or "full time" in desc_lower:
                                is_full_time = True
                                
                    time.sleep(1)
                except Exception as desc_e:
                    print(f"Erro ao buscar detalhes da vaga {job_id}: {desc_e}")
                    
                # Ensure the description text has >= 500 characters and is full-time
                if is_full_time and len(description_text) >= 500:
                    desc_lower = description_text.lower()
                    if not any(k in desc_lower for k in ["tempo integral", "full-time", "full time"]):
                        description_text += "\n\nTipo de vaga: Tempo integral"
                    jobs.append({
                        "platform": "LinkedIn",
                        "title": title,
                        "company": company,
                        "budget": "A Combinar",
                        "link": link,
                        "job_type": "CLT",
                        "profession": keyword,
                        "level": level,
                        "requirements": description_text
                    })
                    
            time.sleep(1)
        except Exception as e:
            print(f"Erro no scraper LinkedIn na página {start}: {e}")
            time.sleep(2)
            
    return jobs
