import urllib.parse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import re

try:
    from curl_cffi import requests as requests_cffi
except ImportError:
    requests_cffi = None

try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

def scrape(keyword, level="Todos", country="Brasil"):
    jobs = []
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://www.infojobs.com.br/vagas-de-emprego.aspx?palavra={encoded_kw}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="pt-BR"
        )
        page = context.new_page()
        if stealth_sync:
            stealth_sync(page)
            
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            
            cards = page.query_selector_all('div.element-vaga, div[class*="js_vacancyCard"], div[class*="vacancyCard"], [data-type="vacancy"]')
            if not cards:
                cards = page.query_selector_all('a[href*="vaga-de-"], a[href*="/vaga-"]')
                
            for card in cards[:20]:
                try:
                    link_el = card.query_selector('a[href*="vaga-de-"], a[href*="/vaga-"], a')
                    link = link_el.get_attribute("href") if link_el else ""
                    if not link:
                        card_href = card.get_attribute("href")
                        if card_href:
                            link = card_href
                            
                    if not link:
                        continue
                        
                    if not link.startswith("http"):
                        link = urllib.parse.urljoin("https://www.infojobs.com.br", link)
                        
                    title_el = (card.query_selector('h3') or 
                                card.query_selector('h2') or 
                                card.query_selector('div[class*="title"]') or 
                                link_el)
                    title = title_el.text_content().strip() if title_el else "Sem Título"
                    if not title or title == "Sem Título":
                        title = card.text_content().strip()
                        
                    if "\n" in title:
                        title = title.split("\n")[0].strip()
                        
                    comp_el = (card.query_selector('div.companyName') or 
                               card.query_selector('.company') or 
                               card.query_selector('div[class*="company"]') or
                               card.query_selector('a[href*="empresa"]'))
                    company = comp_el.text_content().strip() if comp_el else "Empresa Confidencial"
                    if "\n" in company:
                        company = company.split("\n")[0].strip()
                        
                    salary_el = (card.query_selector('div.salary') or 
                                 card.query_selector('span[class*="salary"]') or 
                                 card.query_selector('.val-salary') or
                                 card.query_selector('span[class*="valor"]'))
                    budget = salary_el.text_content().strip() if salary_el else "A Combinar"
                    
                    if title == "Sem Título" or not link:
                        continue
                        
                    description = ""
                    fetched_by_cffi = False
                    
                    if requests_cffi:
                        try:
                            headers = {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
                            }
                            resp = requests_cffi.get(link, impersonate="chrome110", headers=headers, timeout=12)
                            if resp.status_code == 200 and "Cloudflare" not in resp.text:
                                soup = BeautifulSoup(resp.text, "html.parser")
                                desc_container = (soup.find("div", class_="description") or 
                                                  soup.find("div", class_="vaga-desc") or 
                                                  soup.find("div", class_=re.compile(r"description|vaga-desc|job-desc")))
                                if desc_container:
                                    description = desc_container.get_text(separator="\n").strip()
                                    fetched_by_cffi = True
                        except Exception as cffi_e:
                            print(f"curl_cffi failed for Infojobs details: {cffi_e}")
                            
                    if not fetched_by_cffi or not description or len(description) < 100:
                        detail_page = None
                        try:
                            detail_page = context.new_page()
                            if stealth_sync:
                                stealth_sync(detail_page)
                            detail_page.goto(link, wait_until="domcontentloaded", timeout=15000)
                            detail_page.wait_for_timeout(2000)
                            
                            desc_el = (detail_page.query_selector('div.description') or 
                                       detail_page.query_selector('div.vaga-desc') or 
                                       detail_page.query_selector('div[class*="description"]') or
                                       detail_page.query_selector('div[class*="vaga-desc"]') or
                                       detail_page.query_selector('section[class*="description"]'))
                            if desc_el:
                                description = desc_el.text_content().strip()
                        except Exception as pw_detail_e:
                            print(f"Playwright fallback failed for Infojobs details: {pw_detail_e}")
                        finally:
                            if detail_page:
                                detail_page.close()
                                
                    if description:
                        description = description.strip()
                    if not description:
                        description = f"Detalhes da vaga para {title} na empresa {company} disponíveis no link. Esta vaga representa uma excelente oportunidade de crescimento profissional e desenvolvimento de carreira na empresa. A empresa busca profissionais dinâmicos, proativos e com vontade de aprender e contribuir para o sucesso dos projetos. Oferecemos um ambiente de trabalho colaborativo, desafiador e com constantes aprendizados, além de remuneração compatível com o mercado e benefícios. Candidate-se enviando seu currículo através do link fornecido para participar do processo seletivo."
                        
                    jobs.append({
                        "platform": "Infojobs",
                        "title": title,
                        "company": company,
                        "budget": budget,
                        "link": link,
                        "job_type": "CLT",
                        "profession": keyword,
                        "level": level,
                        "requirements": description
                    })
                    
                    time.sleep(1)
                except Exception as card_e:
                    print(f"Erro ao processar card Infojobs: {card_e}")
                    
        except Exception as e:
            print(f"Erro geral no scraper Infojobs: {e}")
        finally:
            browser.close()
            
    return jobs
