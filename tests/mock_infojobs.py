def scrape(keyword, level="Todos"):
    """
    Mock scraper for InfoJobs conforming to the standard scraper contract.
    Returns a list of job dicts matching the keyword and experience level.
    """
    # Generating a description that is at least 500 characters to comply with criteria
    description = (
        f"Procura-se profissional com conhecimento em {keyword} para início imediato no nível {level}. "
        "Esta oportunidade visa integrar um programador experiente focado na criação de microsserviços, "
        "resolução de gargalos de desempenho e implementação de testes unitários automatizados. "
        "É essencial ter conhecimentos em bancos de dados SQL Server ou PostgreSQL, "
        "capacidade de analisar requisitos complexos de negócios e transformá-los em código limpo. "
        "Trabalho dinâmico e focado em metas de entrega contínua. "
        "A empresa oferece plano médico, seguro de vida corporativo, auxílio home-office e "
        "plano de carreira estruturado para crescimento profissional rápido."
    )
    # Ensure description is long enough
    while len(description) < 550:
        description += " Desejável conhecimento em metodologias ágeis e ferramentas de versionamento de código git."

    return [
        {
            "platform": "InfoJobs",
            "title": f"Analista de Sistemas {keyword} {level}" if level != "Todos" else f"Especialista {keyword}",
            "company": "InfoJobs Mock S/A",
            "budget": "R$ 6.500,00 a R$ 9.000,00",
            "link": f"https://www.infojobs.com.br/job/mock-infojobs-{keyword.lower()}-{level.lower()}-777",
            "job_type": "PJ",
            "profession": keyword,
            "level": level,
            "requirements": description
        }
    ]
