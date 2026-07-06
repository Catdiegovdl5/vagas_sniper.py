import re
import html
import json

with open('workana_test.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = html.unescape(text)

# Procure [{ "slug": ...
match = re.search(r'(\[\{"slug":"[^"]+","title":.*?\}\])', text)
if match:
    try:
        arr = json.loads(match.group(1))
        print("Projetos achados:", len(arr))
        for p in arr[:3]:
            print(p.get('title'), " - ", p.get('url'))
    except Exception as e:
        print("Erro JSON:", e)
else:
    print("Nao achou array de projetos")
