import requests
from bs4 import BeautifulSoup

url = 'https://www.workana.com/jobs?query=Gestor%20de%20Tr%C3%A1fego'
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)
print("Status:", r.status_code)
print("Tamanho HTML:", len(r.text))
soup = BeautifulSoup(r.text, 'lxml')
print(f'Divs com class=project-item: {len(soup.find_all("div", class_="project-item"))}')
print(f'Divs com class=project-card: {len(soup.find_all("div", class_="project-card"))}')
print(f'Divs com class=project-body: {len(soup.find_all("div", class_="project-body"))}')
print(f'Qualquer class project: {len(soup.find_all(class_=lambda x: x and "project" in x))}')

# Save to html for grep
with open("workana_test.html", "w", encoding="utf-8") as f:
    f.write(r.text)
