import re
import html
import json

with open('workana_test.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Ache as posições da string "Gestor"
positions = [m.start() for m in re.finditer(r'Gestor', text, re.IGNORECASE)]
print(f"Encontrou {len(positions)} ocorrencias de 'Gestor'.")
for pos in positions[:3]:
    start = max(0, pos - 100)
    end = min(len(text), pos + 100)
    print(f"--- Contexto em {pos} ---")
    print(text[start:end])
