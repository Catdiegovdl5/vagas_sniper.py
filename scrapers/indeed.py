import urllib.parse
from playwright.sync_api import sync_playwright
import re
import json
import time
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as requests_cffi
except ImportError:
    requests_cffi = None

try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

def scrape(keyword, level="Todos", country="Brasil"):
    if "Londrina" in country:
        loc_param = "&l=Londrina%2C+PR&radius=15"
    elif "Assaí" in country:
        loc_param = "&l=Assa%C3%AD%2C+PR&radius=15"
    else:
        loc_param = ""
        
    jobs = []
    encoded_kw = urllib.parse.quote(keyword)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        if stealth_sync:
            stealth_sync(page)
        
        for start in [0, 10]:
            url = f"https://br.indeed.com/jobs?q={encoded_kw}{loc_param}&start={start}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=25000)
                content = page.content()
                
                # Cloudflare check
                if "Cloudflare" in content or "Please wait..." in content:
                    page.wait_for_timeout(5000)
                    content = page.content()
                
                match = re.search(r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.*?\});', content)
                if match:
                    data = json.loads(match.group(1))
                    results = data.get("metaData", {}).get("mosaicProviderJobCardsModel", {}).get("results", [])
                    
                    for r in results:
                        title = r.get("title", "Sem Título")
                        company = r.get("company", "Empresa Confidencial")
                        jobkey = r.get("jobkey", "")
                        link = f"https://br.indeed.com/viewjob?jk={jobkey}" if jobkey else ""
                        snippet = r.get("snippet", "")
                        clean_snippet = re.sub('<[^<]+>', '', snippet)
                        location = r.get("formattedLocation", "Remoto/Brasil")
                        salary = r.get("salarySnippet", {}).get("text", "A Combinar")
                        
                        if title != "Sem Título" and link:
                            # Fetch full description
                            description = ""
                            fetched_by_cffi = False
                            
                            # 1. Try curl_cffi
                            if jobkey and requests_cffi:
                                try:
                                    headers = {
                                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                                        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                                        "Referer": "https://br.indeed.com/"
                                    }
                                    detail_url = f"https://br.indeed.com/viewjob?jk={jobkey}"
                                    resp = requests_cffi.get(detail_url, impersonate="chrome110", headers=headers, timeout=12)
                                    if resp.status_code == 200 and "Cloudflare" not in resp.text and "Please wait..." not in resp.text:
                                        soup = BeautifulSoup(resp.text, "html.parser")
                                        # Tentar múltiplos seletores (Indeed muda o HTML frequentemente)
                                        desc_el = (
                                            soup.find(id="jobDescriptionText") or
                                            soup.find(attrs={"data-testid": "jobDescriptionText"}) or
                                            soup.find(attrs={"data-testid": "job-description"}) or
                                            soup.find(class_=lambda c: c and "jobsearch-jobDescriptionText" in c) or
                                            soup.find(class_=lambda c: c and "job-description" in c) or
                                            soup.find(class_=lambda c: c and "jobDescription" in c)
                                        )
                                        if desc_el:
                                            description = desc_el.get_text(separator="\n").strip()
                                            fetched_by_cffi = True
                                except Exception as cffi_e:
                                    print(f"curl_cffi failed for Indeed job {jobkey}: {cffi_e}")
                            
                            # 2. Fallback to Playwright new context
                            if jobkey and (not fetched_by_cffi or not description or len(description) < 100):
                                detail_context = None
                                detail_page = None
                                try:
                                    detail_context = browser.new_context(
                                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                        viewport={"width": 1280, "height": 800},
                                        locale="pt-BR"
                                    )
                                    detail_page = detail_context.new_page()
                                    if stealth_sync:
                                        stealth_sync(detail_page)
                                        
                                    detail_page.goto(f"https://br.indeed.com/viewjob?jk={jobkey}", wait_until="domcontentloaded", timeout=20000)
                                    
                                    # Tentar múltiplos seletores em cascata
                                    SELECTORS = [
                                        "#jobDescriptionText",
                                        "[data-testid='jobDescriptionText']",
                                        "[data-testid='job-description']",
                                        ".jobsearch-jobDescriptionText",
                                        ".job-description",
                                        "[class*='jobDescription']",
                                        "[class*='JobDescription']",
                                    ]
                                    desc_el = None
                                    for sel in SELECTORS:
                                        try:
                                            detail_page.wait_for_selector(sel, timeout=10000)
                                            desc_el = detail_page.query_selector(sel)
                                            if desc_el:
                                                break
                                        except Exception:
                                            continue
                                    
                                    if desc_el:
                                        description = desc_el.text_content().strip()
                                except Exception as pw_e:
                                    print(f"Playwright fallback failed for Indeed job {jobkey}: {pw_e}")
                                finally:
                                    if detail_page:
                                        detail_page.close()
                                    if detail_context:
                                        detail_context.close()
                                        
                            if not description:
                                description = f"Local: {location}. Resumo: {clean_snippet}"
                                
                            jobs.append({
                                "platform": "Indeed",
                                "title": title,
                                "company": company,
                                "budget": salary,
                                "link": link,
                                "job_type": "CLT",
                                "profession": keyword,
                                "level": level,
                                "requirements": description
                            })
                            time.sleep(1)
            except Exception as e:
                print(f"Erro no scraper Indeed Playwright na página {start}: {e}")
                
        browser.close()
            
    return jobs
