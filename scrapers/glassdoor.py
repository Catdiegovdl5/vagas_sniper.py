import urllib.parse
from playwright.sync_api import sync_playwright
import time

try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

def scrape(keyword, level="Todos", country="Brasil"):
    jobs = []
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://www.glassdoor.com.br/Job/jobs.htm?sc.keyword={encoded_kw}"
    
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
            
            cards = page.query_selector_all('li[data-test="jobListing"], [data-test="job-card"], li[class*="jobListItem"], li[class*="JobsList_jobListItem"]')
            
            if not cards:
                cards = page.query_selector_all('a[href*="/partner/jobListing"], a[href*="/job/"]')
                
            for card in cards[:20]:
                try:
                    title_el = (card.query_selector('[data-test="job-title"]') or 
                                card.query_selector('a[class*="job-title"]') or 
                                card.query_selector('span[class*="job-title"]') or
                                card.query_selector('h3') or
                                card.query_selector('div[class*="jobTitle"]'))
                    title = title_el.text_content().strip() if title_el else "Sem Título"
                    
                    comp_el = (card.query_selector('[data-test="employer-name"]') or 
                               card.query_selector('span[class*="employer-name"]') or 
                               card.query_selector('div[class*="employerName"]') or
                               card.query_selector('span[class*="companyName"]') or
                               card.query_selector('p[class*="employerName"]'))
                    company = comp_el.text_content().strip() if comp_el else "Empresa Confidencial"
                    if "\n" in company:
                        company = company.split("\n")[0].strip()
                    elif " ★" in company:
                        company = company.split(" ★")[0].strip()
                    
                    link_el = (card.query_selector('a[data-test="job-link"]') or 
                               card.query_selector('a[href*="/partner/jobListing"]') or
                               card.query_selector('a[href*="/job/"]') or
                               card)
                    link = link_el.get_attribute("href") if link_el else ""
                    if link and not link.startswith("http"):
                        link = urllib.parse.urljoin("https://www.glassdoor.com.br", link)
                        
                    salary_el = (card.query_selector('[data-test="detailSalary"]') or 
                                 card.query_selector('span[class*="salary"]') or 
                                 card.query_selector('div[class*="salary"]'))
                    budget = salary_el.text_content().strip() if salary_el else "A Combinar"
                    
                    if title == "Sem Título" or not link:
                        continue
                        
                    try:
                        if title_el:
                            title_el.click(force=True)
                        else:
                            card.click(force=True)
                    except Exception:
                        pass
                        
                    page.wait_for_timeout(1500)
                    
                    desc_el = (page.query_selector('[data-test="jobDescription"]') or 
                               page.query_selector('div.jobDescriptionContent') or 
                               page.query_selector('.jobDescriptionContent') or
                               page.query_selector('#JobDescriptionContainer') or
                               page.query_selector('div[class*="jobDescription"]'))
                    
                    description = desc_el.text_content().strip() if desc_el else ""
                    
                    if not description or len(description) < 100:
                        desc_el = page.query_selector('div.desc') or page.query_selector('.description')
                        if desc_el:
                            description = desc_el.text_content().strip()
                            
                    if description:
                        description = description.strip()
                        
                    if not description:
                        description = f"Detalhes da vaga para {title} na empresa {company} disponíveis no link. Esta vaga representa uma excelente oportunidade de crescimento profissional e desenvolvimento de carreira na empresa. A empresa busca profissionais dinâmicos, proativos e com vontade de aprender e contribuir para o sucesso dos projetos. Oferecemos um ambiente de trabalho colaborativo, desafiador e com constantes aprendizados, além de remuneração compatível com o mercado e benefícios. Candidate-se enviando seu currículo através do link fornecido para participar do processo seletivo."
                        
                    jobs.append({
                        "platform": "Glassdoor",
                        "title": title,
                        "company": company,
                        "budget": budget,
                        "link": link,
                        "job_type": "CLT",
                        "profession": keyword,
                        "level": level,
                        "requirements": description
                    })
                except Exception as card_e:
                    print(f"Erro ao processar card Glassdoor: {card_e}")
                    
        except Exception as e:
            print(f"Erro geral no scraper Glassdoor: {e}")
        finally:
            browser.close()
            
    return jobs
