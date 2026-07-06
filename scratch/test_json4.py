import re

with open('workana_test.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('contratacao-de-gestores-de-trafego')
if pos != -1:
    print(text[max(0, pos-200):pos+100])
else:
    print("Nao achou")
