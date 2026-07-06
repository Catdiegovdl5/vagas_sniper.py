# Milestone 2: S-Tier Scrapers & Snippet Bypass Analysis

## 1. Executive Summary
This report analyzes the scraping infrastructure, Python environment, existing scrapers, and proposes detailed implementation plans for the S-Tier Scrapers & Snippet Bypass milestone. We investigated the dependencies, selectors, and bypass mechanisms to allow extracting full job descriptions instead of limited snippets, ensuring high-fidelity matching via Groq AI.

---

## 2. Python Environment & Dependency Verification

We inspected the Python environment and determined the availability of crucial libraries and Playwright browsers:

### Installed Packages
- **`requests` (v2.34.2)**: Present.
- **`beautifulsoup4` (bs4)**: Present.
- **`curl_cffi`**: Present. Very useful for bypassing Cloudflare and TLS fingerprints without launching full browser instances.
- **`playwright` (v1.60.0)**: Present.
- **`playwright-stealth` (v2.0.3)**: Present! Crucial for bypassing anti-bot checks (Cloudflare, Glassdoor, etc.).
- **`python-jobspy` (v1.1.82)**: Present! S-tier scraper library that can fetch jobs from Indeed, LinkedIn, Glassdoor, and ZipRecruiter.
- **`selenium` (v4.45.0)**: Present (available if needed, though Playwright is preferred).
- **`tls-client` (v1.0.1)**: Present.
- **`primp` (v1.3.0)**: Present (Rust-based HTTP client impersonator).

### Playwright Browser Status
- **Chromium**: **Installed and fully functional**.
- **Firefox**: **Not installed** (executable missing at `C:\Users\99196\AppData\Local\ms-playwright\firefox-1522\firefox\firefox.exe`).
- **Webkit**: **Not installed** (executable missing at `C:\Users\99196\AppData\Local\ms-playwright\webkit-2287\Playwright.exe`).

> **Actionable Recommendation**: All Playwright flows must target **Chromium** as it is the only browser binary currently available in the environment.

---

## 3. Review of Existing Scrapers

1. **LinkedIn (`scrapers/linkedin.py`)**:
   - Currently queries the anonymous guest API search endpoint: `https://br.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search`.
   - Only extracts basic job details (title, company, link, location) from the search cards.
   - For `requirements` (descriptions), it uses a static placeholder: `f"Localização: {location} (Vaga encontrada via LinkedIn Ghost API. Detalhes completos direto na página da vaga)."`. This limits the effectiveness of the AI filter.

2. **Indeed (`scrapers/indeed.py`)**:
   - Currently uses Playwright to load the search page and extracts search results from the embedded JSON object `window.mosaic.providerData["mosaic-provider-jobcards"]`.
   - Extracts only the `snippet` field from the search card data.
   - Does not fetch the full description page.

3. **Jooble (`scrapers/jooble.py`)**:
   - Currently queries Jooble's REST API using a hardcoded key.
   - Extracts the search card `snippet` and truncates it to 150 characters.
   - The job links returned by the API are tracking/redirect URLs which are not resolved to the final landing page.

4. **Glassdoor & Infojobs**:
   - Do not have existing scraper scripts in `scrapers/`.

---

## 4. Snippet Bypass & Selector Investigation

To provide the Groq AI filter with complete descriptions, we analyzed the following techniques and selectors:

### A. LinkedIn (Guest API Details)
Instead of loading the full job page (which triggers logins/walls), we can query the public guest details API:
`https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}`
- **Extraction of `job_id`**: Extract from the card's `data-entity-urn` attribute (`urn:li:jobPosting:3983279183` -> `3983279183`) or parse the numeric suffix in the card's link.
- **Description Selector**: The description is wrapped in a container with class `show-more-less-html__markup` or `description__text`.

### B. Indeed (Full Details Page)
- **Detail URL**: `https://br.indeed.com/viewjob?jk={jobkey}`
- **Extraction of `jobkey`**: Readily available in the search JSON response.
- **Description Selector**: `#jobDescriptionText`.
- **Bypass Technique**: Since Indeed has Cloudflare, we can fetch detail pages using `curl_cffi` (impersonating `chrome110`). If it blocks, fall back to navigating our existing Playwright browser instance.

### C. Jooble (Redirect Resolution)
- **Technique**: Perform an HTTP GET request to the Jooble tracking URL with `allow_redirects=True`.
- **Destination Extraction**: Extract the final landing page URL from the response.
- **Description Selector**: 
  - If landing page is on Jooble itself (`jooble.org/desc/...`): use `div.vacancy-desc_text_wrapper` or `div._3lhV3X` or `div[data-role="job-description"]`.
  - If landing page is external (e.g. Gupy, Catho, indeed): apply platform-specific selectors (like `#job-description` for Gupy or `#jobDescriptionText` for Indeed).
  - Generic fallback: Extract all paragraph/list text from container elements with class/id containing `"desc"`, `"job"`, or `"vaga"`.

### D. Glassdoor (Stealth Playwright Flow)
- **Universal Search URL**: `https://www.glassdoor.com.br/Job/jobs.htm?sc.keyword={encoded_keyword}`
- **Bypass Technique**: Initialize Playwright in stealth mode using `playwright-stealth`.
- **Selectors**:
  - Cards container: `li[data-test="jobListing"]` or `article[data-test="job-card"]`.
  - Title: `a[data-test="job-title"]`.
  - Company: `[data-test="employer-name"]`.
  - Location: `[data-test="location"]`.
  - Description: Trigger a click on each card to open the split-screen detail pane, then extract text from `[data-test="jobDescription"]`, `div.jobDescriptionContent`, or `div[class*="JobDetails_jobDescription"]`.

### E. Infojobs (Stealth Playwright + curl_cffi Detail Fallback)
- **Search URL**: `https://www.infojobs.com.br/vagas-de-emprego.aspx?palavra={encoded_keyword}`
- **Bypass Technique**: Cloudflare is highly active. Run search via Playwright with stealth mode.
- **Selectors**:
  - Cards: `div.element-vaga`.
  - Title: `h2` or `a.vaga`.
  - Link: `a` tag inside the card (needs prepending `https://www.infojobs.com.br` if relative).
  - Company: `div.vaga-company`.
  - Location: `div.vaga-local`.
  - Description: Visit `link` page. Fetch detail page HTML via `curl_cffi` (fast, concurrent) and parse `div.description` or `div.vaga-desc`. Fallback to Playwright page navigation if curl_cffi is blocked.

---

## 5. Proposed Code Blueprints (For the Worker)

To guide the implementation phase, here are detailed blueprints/templates for each scraper:

### A. LinkedIn Scraper Blueprint (`scrapers/linkedin.py`)
```python
import urllib.parse
import time
import re
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

def fetch_full_description(job_id):
    """Fetches the full description using the anonymous guest detail API."""
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        # Using curl_cffi impersonate to prevent potential blocks
        response = curl_requests.get(url, impersonate="chrome110", headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            desc_el = soup.find("div", class_="show-more-less-html__markup") or soup.find("div", class_="description__text")
            if desc_el:
                return desc_el.text.strip()
    except Exception as e:
        print(f"Error fetching LinkedIn description for job_id {job_id}: {e}")
    return None

def scrape(keyword, level="Todos", country="Brasil"):
    if "Londrina" in country:
        loc_param = "Londrina%2C%20Paran%C3%A1%2C%20Brasil"
    elif "Assaí" in country:
        loc_param = "Assa%C3%AD%2C%20Paran%C3%A1%2C%20Brasil"
    else:
        loc_param = "Brasil"
        
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    encoded_kw = urllib.parse.quote(keyword)
    
    for start in [0, 25]:
        url = f"https://br.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_kw}&location={loc_param}&start={start}"
        try:
            response = curl_requests.get(url, impersonate="chrome110", headers=headers, timeout=10)
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.find_all("li")
            
            for card in cards:
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
                
                # Extract job ID
                job_id = None
                # Method 1: data-entity-urn
                entity_urn_el = card.find("div", {"data-entity-urn": True})
                if entity_urn_el:
                    job_id = entity_urn_el.get("data-entity-urn", "").split(":")[-1]
                if not job_id:
                    # Method 2: data-id attribute on li element
                    job_id = card.get("data-id")
                if not job_id and link:
                    # Method 3: Regex match from URL
                    match = re.search(r'/view/.*?(\d+)', link)
                    if match:
                        job_id = match.group(1)
                    else:
                        match = re.search(r'-(\d+)(?:\?|$)', link)
                        if match:
                            job_id = match.group(1)
                
                # Retrieve full description if job_id is parsed
                description = None
                if job_id:
                    description = fetch_full_description(job_id)
                    time.sleep(1.5)  # Throttle to avoid rate limits
                    
                if not description:
                    description = f"Localização: {location}. Verifique a descrição completa no link."

                if title != "Sem Título" and link:
                    jobs.append({
                        "platform": "LinkedIn",
                        "title": title,
                        "company": company,
                        "budget": "A Combinar",
                        "link": link,
                        "job_type": "Diversos",
                        "profession": keyword,
                        "level": level,
                        "requirements": description
                    })
            time.sleep(1)
        except Exception as e:
            print(f"Error in LinkedIn scraper at start={start}: {e}")
            
    return jobs
```

### B. Indeed Scraper Blueprint (`scrapers/indeed.py`)
```python
import urllib.parse
import re
import json
import random
from playwright.sync_api import sync_playwright
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

def fetch_description_via_curl(jobkey):
    """Fast Cloudflare-bypass fetch for Indeed job details."""
    url = f"https://br.indeed.com/viewjob?jk={jobkey}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        r = curl_requests.get(url, headers=headers, impersonate="chrome110", timeout=8)
        if r.status_code == 200 and "jobDescriptionText" in r.text:
            soup = BeautifulSoup(r.text, "html.parser")
            desc_el = soup.find(id="jobDescriptionText")
            if desc_el:
                return desc_el.text.strip()
    except Exception as e:
        print(f"curl_cffi failed for jk={jobkey}: {e}")
    return None

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
        # Launch Chromium (only browser binary installed)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for start in [0, 10]:
            url = f"https://br.indeed.com/jobs?q={encoded_kw}{loc_param}&start={start}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                content = page.content()
                
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
                        
                        if title != "Sem Título" and jobkey:
                            # 1. Try curl_cffi first (faster, concurrent-friendly)
                            description = fetch_description_via_curl(jobkey)
                            
                            # 2. Fall back to Playwright if blocked
                            if not description:
                                try:
                                    detail_page = context.new_page()
                                    detail_page.goto(link, wait_until="domcontentloaded", timeout=10000)
                                    detail_page.wait_for_selector("#jobDescriptionText", timeout=4000)
                                    description = detail_page.locator("#jobDescriptionText").inner_text().strip()
                                    detail_page.close()
                                    page.wait_for_timeout(random.randint(1000, 2000))
                                except Exception as e_play:
                                    print(f"Playwright detail fetch failed for {jobkey}: {e_play}")
                                    description = f"Local: {location}. Resumo: {clean_snippet}"
                            
                            jobs.append({
                                "platform": "Indeed",
                                "title": title,
                                "company": company,
                                "budget": salary,
                                "link": link,
                                "job_type": "Diversos",
                                "profession": keyword,
                                "level": level,
                                "requirements": description
                            })
            except Exception as e:
                print(f"Error in Indeed scraper at start={start}: {e}")
                
        browser.close()
            
    return jobs
```

### C. Jooble Scraper Blueprint (`scrapers/jooble.py`)
```python
import requests
import re
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

def resolve_and_extract_description(redirect_url):
    """Follows tracking redirects and parses description based on landing page domain."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        # Resolve redirect chain to target domain
        r = requests.get(redirect_url, headers=headers, timeout=10, allow_redirects=True)
        final_url = r.url
        html = r.text
        
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. If final landing page is a Jooble detail page
        if "jooble.org" in final_url:
            desc_el = (soup.find(attrs={"itemprop": "description"}) or 
                       soup.find("div", class_="vacancy-desc_text_wrapper") or
                       soup.find("div", class_="_3lhV3X") or
                       soup.find("div", {"data-role": "job-description"}))
            if desc_el:
                return desc_el.text.strip(), final_url
                
        # 2. If it redirected to Gupy
        elif "gupy.io" in final_url:
            desc_el = soup.find(id="job-description") or soup.find("div", class_="description")
            if desc_el:
                return desc_el.text.strip(), final_url
                
        # 3. If it redirected to Indeed
        elif "indeed.com" in final_url:
            desc_el = soup.find(id="jobDescriptionText")
            if desc_el:
                return desc_el.text.strip(), final_url
                
        # 4. Generic fallback extractor
        for s in soup(["script", "style", "nav", "footer", "header"]):
            s.decompose()
        candidates = []
        for el in soup.find_all(["div", "section"]):
            class_str = " ".join(el.get("class", [])).lower()
            id_str = el.get("id", "").lower()
            if any(term in class_str or term in id_str for term in ["desc", "job", "vaga", "requisito"]):
                text = el.text.strip()
                if len(text) > 200:
                    candidates.append((len(text), el))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1].text.strip(), final_url
            
        # Return fallback text
        return soup.text.strip()[:1000], final_url
    except Exception as e:
        print(f"Error resolving redirect {redirect_url}: {e}")
    return None, redirect_url

def scrape(keyword, level, country="Brasil"):
    jobs = []
    try:
        search_kw = f"{keyword}"
        if level != "Todos":
            search_kw += f" {level}"
            
        base_url = "jooble.org"
        loc = ""
        if country == "Brasil" or "Brasil" in country: 
            base_url = "br.jooble.org"
            loc = "Brazil"
            
        url = f"https://{base_url}/api/0031603e-bd0a-4505-ad10-383c420d804f"
        payload = {
            "keywords": search_kw,
            "location": loc,
            "page": "1"
        }
        headers = {"Content-type": "application/json"}
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
        
        if data.get("jobs"):
            for item in data["jobs"][:15]:  # Process top 15 to minimize redirect overhead
                title = item.get("title", "Sem título")
                j_type = "PJ" if "PJ" in title.upper() else "CLT"
                tracking_link = item.get("link", "#")
                
                description = None
                final_link = tracking_link
                if tracking_link and tracking_link != "#":
                    description, final_link = resolve_and_extract_description(tracking_link)
                    
                if not description:
                    # Fallback to API snippet
                    snippet = item.get("snippet", "")
                    description = re.sub('<[^<]+>', '', snippet).replace('\n', ' ')
                    
                jobs.append({
                    "platform": "Jooble",
                    "title": title,
                    "company": item.get("company", "Confidencial"),
                    "budget": item.get("salary") or "A Combinar",
                    "link": final_link,
                    "job_type": j_type,
                    "profession": keyword,
                    "level": level,
                    "requirements": description
                })
    except Exception as e:
        print("Error Jooble:", e)
        
    return jobs
```

### D. Glassdoor Scraper Blueprint (`scrapers/glassdoor.py`)
```python
import urllib.parse
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from bs4 import BeautifulSoup

def scrape(keyword, level="Todos", country="Brasil"):
    jobs = []
    encoded_kw = urllib.parse.quote(keyword)
    # Universal search url that auto-redirects to local search paths
    url = f"https://www.glassdoor.com.br/Job/jobs.htm?sc.keyword={encoded_kw}"
    
    with sync_playwright() as p:
        # Target chromium browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page)
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(random.randint(2000, 4000))
            
            # Select job listings
            job_cards = page.locator('li[data-test="jobListing"]').all()
            if not job_cards:
                job_cards = page.locator('article[data-test="job-card"]').all()
                
            for card in job_cards[:12]:
                try:
                    title_el = card.locator('a[data-test="job-title"]')
                    if title_el.count() == 0:
                        continue
                    title = title_el.inner_text().strip()
                    link = title_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.glassdoor.com.br" + link
                        
                    company_el = card.locator('[data-test="employer-name"]')
                    company = company_el.inner_text().split("\n")[0].strip() if company_el.count() > 0 else "Confidencial"
                    
                    loc_el = card.locator('[data-test="location"]')
                    location = loc_el.inner_text().strip() if loc_el.count() > 0 else "Brasil"
                    
                    # Click card to load details pane on the right side
                    card.click()
                    page.wait_for_timeout(random.randint(1500, 2500))
                    
                    # Target description selector
                    desc_el = (page.locator('[data-test="jobDescription"]') or 
                               page.locator('div.jobDescriptionContent') or 
                               page.locator('div[class*="JobDetails_jobDescription"]'))
                    
                    desc_text = desc_el.inner_text().strip() if desc_el.count() > 0 else ""
                    
                    if title and link:
                        jobs.append({
                            "platform": "Glassdoor",
                            "title": title,
                            "company": company,
                            "budget": "A Combinar",
                            "link": link,
                            "job_type": "Diversos",
                            "profession": keyword,
                            "level": level,
                            "requirements": desc_text or f"Detalhes na página da vaga. Local: {location}."
                        })
                except Exception as card_err:
                    print(f"Error parsing Glassdoor card: {card_err}")
        except Exception as e:
            print(f"Glassdoor scraper failed: {e}")
        finally:
            browser.close()
            
    return jobs
```

### E. Infojobs Scraper Blueprint (`scrapers/infojobs.py`)
```python
import urllib.parse
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

def fetch_infojobs_details(detail_url):
    """Attempts to fetch detail page via curl_cffi to bypass browser page overhead."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = curl_requests.get(detail_url, impersonate="chrome120", headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            desc_el = (soup.find("div", class_="description") or 
                       soup.find("div", class_="vaga-desc") or 
                       soup.find(id="vagaDescription"))
            if desc_el:
                return desc_el.text.strip()
    except Exception as e:
        print(f"curl_cffi failed for InfoJobs detail {detail_url}: {e}")
    return None

def scrape(keyword, level="Todos", country="Brasil"):
    jobs = []
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://www.infojobs.com.br/vagas-de-emprego.aspx?palavra={encoded_kw}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page)
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            # Wait for job cards
            page.wait_for_selector("div.element-vaga", timeout=10000)
            
            cards = page.locator("div.element-vaga").all()
            for card in cards[:12]:
                try:
                    title_el = card.locator("h2")
                    title = title_el.inner_text().strip() if title_el.count() > 0 else "Sem Título"
                    
                    link_el = card.locator("a").first
                    link = link_el.get_attribute("href") if link_el.count() > 0 else ""
                    if link and not link.startswith("http"):
                        link = "https://www.infojobs.com.br" + link
                        
                    company_el = card.locator("div.vaga-company")
                    company = company_el.inner_text().strip() if company_el.count() > 0 else "Confidencial"
                    
                    # 1. Fetch description via curl_cffi
                    description = None
                    if link:
                        description = fetch_infojobs_details(link)
                        
                    # 2. Fall back to Playwright navigation if curl_cffi fails
                    if not description and link:
                        try:
                            detail_page = context.new_page()
                            detail_page.goto(link, wait_until="domcontentloaded", timeout=12000)
                            desc_sel = detail_page.locator("div.description")
                            if desc_sel.count() == 0:
                                desc_sel = detail_page.locator("div.vaga-desc")
                            description = desc_sel.inner_text().strip() if desc_sel.count() > 0 else ""
                            detail_page.close()
                            page.wait_for_timeout(random.randint(1000, 2000))
                        except Exception as e_play:
                            print(f"Playwright fallback failed for InfoJobs detail: {e_play}")
                            
                    if title and link:
                        jobs.append({
                            "platform": "Infojobs",
                            "title": title,
                            "company": company,
                            "budget": "A Combinar",
                            "link": link,
                            "job_type": "Diversos",
                            "profession": keyword,
                            "level": level,
                            "requirements": description or "Detalhes na página da vaga."
                        })
                except Exception as card_err:
                    print(f"Error parsing InfoJobs card: {card_err}")
        except Exception as e:
            print(f"InfoJobs scraper failed: {e}")
        finally:
            browser.close()
            
    return jobs
```

---

## 6. Implementation Architecture

To ensure the new and updated scrapers integrate seamlessly into `bot.py` without breaking existing workflows:

1. **Scraper Signatures**:
   All new scrapers should define the standard signature:
   `def scrape(keyword, level="Todos", country="Brasil")`

2. **Integration in `bot.py`**:
   In `bot.py`, add `glassdoor` and `infojobs` to the `user_settings["platforms"]` dictionary:
   ```python
   "platforms": {
       ...
       "glassdoor": True,
       "infojobs": True,
       ...
   }
   ```
   Add them to the lists that receive the `country` parameter inside the search loop:
   ```python
   if plat in ['jsearch', 'jooble', 'github_vagas', 'novenove', 'freelancer', 'meta_ads', 'indeed', 'linkedin', 'gmail', 'glassdoor', 'infojobs']:
       jobs = await asyncio.to_thread(module.scrape, keyword=keyword, level=user_settings["level"], country=user_settings["location"])
   ```

3. **Rate Limiting & Safety**:
   Introduce random sleep delays (1s to 3s) during detail fetches. Playwright should be used with a randomized viewport and stealth configuration (`stealth_sync`).
