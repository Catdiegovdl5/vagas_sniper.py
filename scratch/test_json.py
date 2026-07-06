import json
from bs4 import BeautifulSoup

with open('workana_test.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'lxml')

tag = soup.find('search-project-list')
if tag and tag.has_attr(':initials'):
    data = json.loads(tag[':initials'])
    print(f"Encontrados {len(data['projects'])} projetos.")
    print("Primeiro:", data['projects'][0]['title'], " | ", data['projects'][0]['url'])
