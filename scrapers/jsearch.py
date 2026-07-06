import requests
import urllib.parse

def scrape(keyword, level, country="Brasil"):
    jobs = []
    try:
        search_kw = f"{keyword}"
        if level != "Todos":
            search_kw += f" {level}"
            
        encoded_kw = urllib.parse.quote(search_kw)
        
        if "Brasil" in country:
            url = f"https://jsearch.p.rapidapi.com/search?query={encoded_kw}&page=1&num_pages=3&date_posted=month&country=br&language=pt"
        elif country == "USA":
            url = f"https://jsearch.p.rapidapi.com/search?query={encoded_kw}&page=1&num_pages=3&date_posted=month&country=us&language=en"
        else:
            url = f"https://jsearch.p.rapidapi.com/search?query={encoded_kw}&page=1&num_pages=3&date_posted=month"
        
        headers = {
            "x-rapidapi-key": "7af3cebf37mshb1adb579644f3d1p1f605fjsn26d9e7a63fe0",
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data.get("data"):
            for item in data["data"][:30]:
                title = item.get("job_title", "Sem título")
                j_type = "PJ" if "PJ" in title.upper() else "CLT"
                
                desc = item.get("job_description", "")
                if len(desc) > 150:
                    req_text = desc[:150].replace('\n', ' ') + "..."
                else:
                    req_text = desc.replace('\n', ' ')
                
                if not req_text.strip():
                    req_text = "Sem descrição disponível."
                
                link = item.get("job_apply_link") or item.get("job_google_link") or "https://google.com"
                
                jobs.append({
                    "platform": f"JSearch",
                    "title": title,
                    "company": item.get("employer_name", "Confidencial"),
                    "budget": "A Combinar",
                    "link": link,
                    "job_type": j_type,
                    "profession": keyword,
                    "level": level,
                    "requirements": req_text
                })
    except Exception as e:
        print("Erro JSearch:", e)
    
    if not jobs:
        jobs.append({
            "platform": "JSearch",
            "title": f"Sem vagas API JSearch para {keyword} ({level})",
            "company": "N/A",
            "budget": "N/A",
            "link": "#",
            "job_type": "N/A",
            "profession": keyword,
            "level": level,
            "requirements": "Não houve resultados."
        })
    return jobs
