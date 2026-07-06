def scrape(keyword, level="Todos"):
    """
    Mock scraper for Glassdoor conforming to the standard scraper contract.
    Returns a list of job dicts matching the keyword and experience level.
    """
    # Generating a description that is at least 500 characters to comply with criteria
    description = (
        f"Conecte-se com a vaga de desenvolvedor especializado em {keyword} no nível {level}. "
        "A empresa busca um profissional altamente capacitado para atuar no desenvolvimento de sistemas, "
        "desenho de arquiteturas escaláveis, e otimização de consultas de banco de dados. "
        "Requisitos desejados incluem experiência com ferramentas de automação, pipelines de CI/CD, "
        "além de boa comunicação para interagir com times multifuncionais e stakeholders. "
        "Oferecemos plano de saúde integral, vale refeição flexível, participação nos lucros, "
        "e flexibilidade de horários em regime totalmente remoto. Venha fazer parte do nosso time!"
    )
    # Ensure description is long enough
    while len(description) < 550:
        description += " Adicionalmente, valorizamos certificações em cloud computing e práticas de segurança."

    return [
        {
            "platform": "Glassdoor",
            "title": f"Senior {keyword} Engineer" if level == "Sênior" else f"{keyword} Developer",
            "company": "Glassdoor Mock Corp",
            "budget": "R$ 8.000,00 a R$ 12.000,00",
            "link": f"https://www.glassdoor.com/job/mock-glassdoor-{keyword.lower()}-{level.lower()}-999",
            "job_type": "CLT",
            "profession": keyword,
            "level": level,
            "requirements": description
        }
    ]
