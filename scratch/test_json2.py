import re
import html
import json

with open('workana_test.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Workana usa vue.js, a tag é <search-project-list :initials="{...}">
match = re.search(r':initials="([^"]+)"', text)
if match:
    data_str = html.unescape(match.group(1))
    try:
        data = json.loads(data_str)
        print("Projetos achados:", len(data.get('projects', [])))
        for p in data.get('projects', [])[:3]:
            print(p['title'], " - ", p['url'])
    except Exception as e:
        print("Erro JSON:", e)
else:
    print("Nao achou tag :initials")
