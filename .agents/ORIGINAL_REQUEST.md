# Original User Request

## Initial Request — 2026-07-04T13:30:56Z

O projeto visa transformar o bot atual em uma máquina autônoma de recrutamento end-to-end com quatro pilares: (1) Adição de Scrapers S-Tier (LinkedIn, Glassdoor, InfoJobs); (2) Web Scraping profundo para resolver a limitação de snippets (Jooble/Indeed); (3) Novo modelo de pontuação IA (priorizando Salário e Benefícios); e (4) Sistema de Auto-Apply para disparo automatizado de currículos.

Working directory: C:\Users\99196\OneDrive\Documentos\vagas_bot
Integrity mode: development

## Requirements

### R1. Scrapers S-Tier
Implementar scrapers para LinkedIn, Glassdoor e InfoJobs. Eles devem ser capazes de puxar o texto completo das vagas. O LinkedIn deve focar em vagas de Full-time e ignorar o restante.

### R2. Bypass de Snippets (Deep Scrape)
Para plataformas que enviam apenas resumos (Jooble e Indeed), construir um mecanismo que acesse a URL da vaga e extraia a descrição completa em HTML/Texto.

### R3. IA Ranking por Remuneração
Modificar a estrutura de dados avaliativa (`JobEvaluation`) para que a IA não apenas "aprove", mas ranqueie as vagas priorizando aquelas que exibem valores salariais e benefícios como VR/VA.

### R4. Motor de Auto-Apply
Criar um módulo capaz de preencher formulários simples de candidatura (Easy Apply) usando os dados do currículo do usuário fornecidos na pasta local.

## Acceptance Criteria

### Scrapers S-Tier & Bypass
- [ ] O script `scrapers/linkedin.py` retorna pelo menos 10 vagas com a chave `requirements` contendo mais de 500 caracteres, rodando um teste unitário programático.
- [ ] O scraper do Indeed resolve e extrai o texto do DOM ao invés de retornar o snippet da API.

### IA Ranking
- [ ] Ao rodar o pipeline do Groq em um dataset de 5 vagas controladas, a vaga com maior salário declarado sempre fica no topo (`ai_score` mais alto).

### Auto-Apply
- [ ] Existe um script `test_apply.py` que demonstra submissão bem sucedida (status 200 OK) para uma URL de mockup local representando um ATS.

## Follow-up — 2026-07-04T15:34:26Z

O projeto visa refinar a inteligência de filtragem da IA (Groq) no `Sniper_bot`, eliminando o problema de "alucinação" onde o modelo reprova a vaga em texto, mas a aprova no booleano. O objetivo é alcançar 110% de precisão usando travas via código (hard-locks), troca de modelo e validação massiva automatizada.

Working directory: C:\Users\99196\OneDrive\Documentos\vagas_bot
Integrity mode: benchmark

## Requirements

### R1. Python Hard-Locks (Trava de Segurança)
Modificar o fluxo de avaliação em `scrapers/ai_filter.py`. Mesmo que a IA retorne `aprovado = True`, o Python deve interceptar a resposta e forçar `aprovado = False` se qualquer uma das regras de quebra for ativada (ex: `vaga_corresponde_ao_cargo == False`, `is_freelance == True`, `localidade_correta == False`, `exige_faculdade == True`, `exige_experiencia == True`).

### R2. Upgrade de Modelo
Alterar o modelo padrão instanciado no `AsyncGroq` (dentro de `ai_filter.py`) para um modelo de maior capacidade de raciocínio (ex: `llama3-70b-8192` or `mixtral-8x7b-32768`) para minimizar as alucinações de inconsistência lógica.

### R3. Bateria de Testes de Sanidade (50 Vagas)
Criar um script de teste e um dataset (JSON ou CSV) com 50 vagas projetadas especificamente como "pegadinhas" (vagas em dólar, vagas que exigem inglês fluente, vagas de estágio quando a configuração é sem formação, projetos Workana, etc). O script deve submeter as 50 vagas ao `ai_filter.py` e gerar um relatório.

## Acceptance Criteria

### Precisão e Blindagem
- [ ] O código Python sobrepõe a decisão da IA quando as regras booleanas falham.
- [ ] O modelo configurado no Groq é de alta capacidade (70B+).
- [ ] O script de teste com 50 vagas executa com sucesso.
- [ ] A taxa de aprovação para as vagas criadas como "pegadinha" no dataset é estritamente 0% (gabarito perfeito de bloqueio).
