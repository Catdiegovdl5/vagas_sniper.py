import requests
import urllib.parse

def scrape(keyword, level="Todos", country="Brasil"):
    jobs = []
    try:
        encoded_kw = urllib.parse.quote(keyword)
        url = f"https://www.freelancer.com/api/projects/0.1/projects/active/?query={encoded_kw}&limit=15"
        
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "projects" in data["result"]:
                for item in data["result"]["projects"]:
                    title = item.get("title") or "Sem título"
                    desc = item.get("description") or "Sem descrição"
                    
                    seo_url = item.get("seo_url", "")
                    link = f"https://www.freelancer.com/projects/{seo_url}" if seo_url else "https://www.freelancer.com"
                    
                    budget_min = item.get("budget", {}).get("minimum") or 0
                    budget_max = item.get("budget", {}).get("maximum") or 0
                    currency = item.get("currency", {}).get("code", "USD")
                    budget_str = f"{currency} {budget_min} - {budget_max}" if budget_max > 0 else "A Combinar"
                    
                    jobs.append({
                        "platform": "Freelancer.com",
                        "title": title,
                        "company": "Cliente Freelancer.com",
                        "budget": f"PJ - {budget_str}",
                        "link": link,
                        "job_type": "Freelance / PJ",
                        "profession": keyword,
                        "level": level,
                        "requirements": desc[:250] + "..." if len(desc) > 250 else desc
                    })
    except Exception as e:
        print("Erro Freelancer.com:", e)
        
    return jobs
