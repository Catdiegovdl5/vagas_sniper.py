from apify_client import ApifyClient
import urllib.parse

import os
APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")

def scrape(keyword, level="Todos", country="Brasil"):
    if country != "Brasil":
        return []

    client = ApifyClient(APIFY_TOKEN)
    
    search_term = keyword
    if not any(word in keyword.lower() for word in ['contratando', 'vaga', 'oportunidade', 'estágio', 'freela', 'pj']):
        search_term = f"vaga {keyword}"

    search_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BR&q={urllib.parse.quote(search_term)}"
    
    run_input = {
        "urls": [{"url": search_url}],
        "startUrls": [{"url": search_url}], 
        "facebookPageUrls": [],
        "adKeyword": search_term,
        "countryCode": "BR",
        "maxAds": 10,
        "adActiveStatus": "ACTIVE"
    }

    jobs = []
    try:
        print(f"[Meta Ads] Iniciando varredura com Apify para o termo: {search_term}...")
        run = client.actor("curious_coder/facebook-ads-library-scraper").call(run_input=run_input)
        
        dataset_id = run["defaultDatasetId"] if isinstance(run, dict) else getattr(run, "defaultDatasetId", getattr(run, "default_dataset_id", None))
        for item in client.dataset(dataset_id).iterate_items():
            text = item.get('primaryText', '') or item.get('content', '')
            if not text and not item.get('linkUrl'):
                continue
                
            if not text:
                text = "Sem descrição"
                
            title = f"💎 Vaga Patrocinada (Meta Ads) - {item.get('pageName', 'Empresa Confidencial')}"
            
            jobs.append({
                "platform": "Meta Ads",
                "title": title,
                "company": item.get('pageName', 'Empresa Confidencial'),
                "budget": "A Combinar (Investimento Ads)",
                "link": item.get('linkUrl') or item.get('urlInAdLibrary', 'https://facebook.com/ads/library'),
                "job_type": "PJ/CLT",
                "profession": keyword,
                "level": level,
                "requirements": text[:350] + "..." if len(text) > 350 else text
            })
    except Exception as e:
        print(f"Erro no Meta Ads (Apify): {e}")
        
    return jobs
