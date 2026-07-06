import asyncio
import sqlite3
import random
import importlib
import PyPDF2
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import sys
sys.path.append(".")
from database import insert_jobs

import os
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7724330024:AAFtoSLgXVDlvNmeyPCVMnkWIqbk4wvLSVg")

import traceback
from loguru import logger

# --- Configurando o Monitoramento Profissional (Loguru) ---
logger.remove() # Remove o handler padrão
logger.add(sys.stderr, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="DEBUG")
logger.add("erros_robo.log", rotation="10 MB", retention="5 days", level="ERROR", 
           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
# ----------------------------------------------------------

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Monitoramento de Erros via Telegram ---
@dp.errors()
async def global_error_handler(event: types.ErrorEvent):
    erro_completo = "".join(traceback.format_exception(type(event.exception), event.exception, event.exception.__traceback__))
    logger.error(f"O robô quebrou: {erro_completo}")
    
    msg = f"🚨 *CRITICAL BUG DETECTED:*\n```python\n{erro_completo[:3900]}\n```"
    if event.update.callback_query:
        await event.update.callback_query.message.answer(msg, parse_mode="Markdown")
    elif event.update.message:
        await event.update.message.answer(msg, parse_mode="Markdown")
# -------------------------------------------

user_settings = {
    "level": "Todos",
    "location": "Brasil (Remoto)",
    "contract": "Todos", # Todos, PJ, CLT, Freelancer
    "education": "Todos", # Todos, Sem Formação
    "modo_freelancer": False,
    "platforms": {
        "jsearch": True,
        "jooble": True,
        "workana": True,
        "remotar": True,
        "novenove": True,
        "freelancer": True,
        "github_vagas": True,
        "meta_ads": True,
        "indeed": True,
        "linkedin": True,
        "glassdoor": True,
        "infojobs": True,
        "gmail": False
    },
    "ai_filter": True
}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await show_main_menu(message)

@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    markup = get_main_menu_markup()
    await callback.message.edit_text("🤖 *Sniper Bot Nativo 100% Operante*\n\nO que você deseja fazer?", reply_markup=markup, parse_mode="Markdown")

async def show_main_menu(message: types.Message):
    markup = get_main_menu_markup()
    await message.answer("🤖 *Sniper Bot Nativo 100% Operante*\n\nO que você deseja fazer?", reply_markup=markup, parse_mode="Markdown")

def get_main_menu_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Caçar Vagas", callback_data="hunt_menu")],
        [InlineKeyboardButton(text="🛠 Configurações", callback_data="settings_menu")]
    ])

# ----------------- CONFIGURAÇÕES -----------------
@dp.callback_query(F.data == "settings_menu")
async def settings_menu(callback: CallbackQuery):
    await callback.message.edit_text("⚙️ *Configurações do Robô*", reply_markup=get_settings_markup(), parse_mode="Markdown")

def get_settings_markup():
    p = user_settings["platforms"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📍 Local: {user_settings['location']} (Mudar)", callback_data="change_location")],
        [InlineKeyboardButton(text=f"Nível: {user_settings['level']} (Mudar)", callback_data="change_level")],
        [InlineKeyboardButton(text=f"Contrato: {user_settings['contract']} (Mudar)", callback_data="change_contract")],
        [InlineKeyboardButton(text=f"Formação: {user_settings['education']} (Mudar)", callback_data="change_education")],
        [InlineKeyboardButton(text=f"👨‍💻 Modo Exclusivo Freelancer: {'✅ ON' if user_settings.get('modo_freelancer', False) else '❌ OFF'}", callback_data="toggle_modo_freelancer")],
        [InlineKeyboardButton(text=f"JSearch: {'✅ ON' if p['jsearch'] else '❌ OFF'}", callback_data="toggle_jsearch"),
         InlineKeyboardButton(text=f"Jooble: {'✅ ON' if p['jooble'] else '❌ OFF'}", callback_data="toggle_jooble")],
        [InlineKeyboardButton(text=f"Workana: {'✅ ON' if p['workana'] else '❌ OFF'}", callback_data="toggle_workana"),
         InlineKeyboardButton(text=f"Remotar: {'✅ ON' if p['remotar'] else '❌ OFF'}", callback_data="toggle_remotar")],
        [InlineKeyboardButton(text=f"99Freelas: {'✅ ON' if p['novenove'] else '❌ OFF'}", callback_data="toggle_novenove"),
         InlineKeyboardButton(text=f"Freelancer: {'✅ ON' if p['freelancer'] else '❌ OFF'}", callback_data="toggle_freelancer")],
        [InlineKeyboardButton(text=f"GitHub Vagas: {'✅ ON' if p['github_vagas'] else '❌ OFF'}", callback_data="toggle_github_vagas"),
         InlineKeyboardButton(text=f"Meta Ads: {'✅ ON' if p['meta_ads'] else '❌ OFF'}", callback_data="toggle_meta_ads")],
        [InlineKeyboardButton(text=f"Indeed: {'✅ ON' if p['indeed'] else '❌ OFF'}", callback_data="toggle_indeed"),
         InlineKeyboardButton(text=f"LinkedIn: {'✅ ON' if p['linkedin'] else '❌ OFF'}", callback_data="toggle_linkedin")],
        [InlineKeyboardButton(text=f"Glassdoor: {'✅ ON' if p['glassdoor'] else '❌ OFF'}", callback_data="toggle_glassdoor"),
         InlineKeyboardButton(text=f"Infojobs: {'✅ ON' if p['infojobs'] else '❌ OFF'}", callback_data="toggle_infojobs")],
        [InlineKeyboardButton(text=f"📧 Gmail Alertas: {'✅ ON' if p['gmail'] else '❌ OFF'}", callback_data="toggle_gmail")],
        [InlineKeyboardButton(text=f"🧠 Filtro IA (Groq): {'✅ ON' if user_settings['ai_filter'] else '❌ OFF'}", callback_data="toggle_ai")],
        [InlineKeyboardButton(text="🔙 Voltar ao Início", callback_data="main_menu")]
    ])

@dp.callback_query(F.data == "change_level")
async def change_level(callback: CallbackQuery):
    levels = ["Todos", "Júnior", "Pleno", "Sênior"]
    idx = levels.index(user_settings["level"])
    user_settings["level"] = levels[(idx + 1) % len(levels)]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup())

@dp.callback_query(F.data == "change_location")
async def change_location(callback: CallbackQuery):
    locations = ["Brasil (Remoto)", "Londrina/PR", "Assaí/PR"]
    idx = locations.index(user_settings["location"])
    user_settings["location"] = locations[(idx + 1) % len(locations)]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup())

@dp.callback_query(F.data == "change_contract")
async def change_contract(callback: CallbackQuery):
    contracts = ["Todos", "PJ", "CLT", "Freelancer"]
    idx = contracts.index(user_settings["contract"])
    user_settings["contract"] = contracts[(idx + 1) % len(contracts)]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup())

@dp.callback_query(F.data == "change_education")
async def change_education(callback: CallbackQuery):
    educations = ["Todos", "Sem Formação"]
    idx = educations.index(user_settings["education"])
    user_settings["education"] = educations[(idx + 1) % len(educations)]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup())

@dp.callback_query(F.data == "toggle_ai")
async def toggle_ai(callback: CallbackQuery):
    user_settings["ai_filter"] = not user_settings["ai_filter"]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup())

@dp.callback_query(F.data == "toggle_modo_freelancer")
async def toggle_modo_freelancer(callback: CallbackQuery):
    is_now_on = not user_settings.get("modo_freelancer", False)
    user_settings["modo_freelancer"] = is_now_on
    
    freelance_plats = ["workana", "novenove", "freelancer"]
    clt_plats = ["jsearch", "jooble", "remotar", "github_vagas", "meta_ads", "indeed", "linkedin", "glassdoor", "infojobs"]
    
    if is_now_on:
        for p in freelance_plats: user_settings["platforms"][p] = True
        for p in clt_plats: user_settings["platforms"][p] = False
        user_settings["contract"] = "Freelancer"
    else:
        for p in freelance_plats: user_settings["platforms"][p] = False
        for p in clt_plats: user_settings["platforms"][p] = True
        user_settings["contract"] = "Todos"
        
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup())

@dp.callback_query(F.data.startswith("toggle_"))
async def toggle_platform(callback: CallbackQuery):
    plat = callback.data.replace("toggle_", "")
    if plat in user_settings["platforms"]:
        user_settings["platforms"][plat] = not user_settings["platforms"][plat]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup())

# ----------------- CAÇAR VAGAS (NICHOS) -----------------
@dp.callback_query(F.data == "hunt_menu")
async def hunt_menu(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Especialista em IA", callback_data="nicho_ai")],
        [InlineKeyboardButton(text="💻 Desenvolvimento", callback_data="nicho_dev")],
        [InlineKeyboardButton(text="📊 Dados & RPA", callback_data="nicho_dados")],
        [InlineKeyboardButton(text="📈 Growth & Mkt", callback_data="nicho_mkt")],
        [InlineKeyboardButton(text="🎬 Audiovisual & Criação", callback_data="nicho_audio")],
        [InlineKeyboardButton(text="🌱 Início de Carreira (Júnior)", callback_data="nicho_junior")],
        [InlineKeyboardButton(text="🔙 Voltar", callback_data="main_menu")]
    ])
    await callback.message.edit_text("🎯 *Selecione o seu Nicho Estratégico:*", reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("nicho_"))
async def show_niche_jobs(callback: CallbackQuery):
    nicho = callback.data.split("_")[1]
    
    menus = {
        "ai": ["Especialista em IA", "Especialista em IA (Conteúdo)", "AI Coder", "Engenheiro de Prompt", "Consultor de IA"],
        "dev": ["Python Scraping", "Integração de APIs", "Backend Python"],
        "dados": ["Analista de BI", "Automação RPA", "Analista de Dados"],
        "mkt": ["Growth Engineer", "Especialista Tracking", "Analista RevOps", "SDR Técnico", "Gestor de Tráfego"],
        "junior": ["Desenvolvedor Júnior", "Analista de Dados Jr", "Assistente de Marketing", "Assistente de Growth", "SDR Junior", "Editor de Vídeo Júnior", "AI Coder Júnior", "Engenheiro de Prompt Jr"],
        "audio": ["Editor de Vídeo", "Video Maker", "Design e Social Media"]
    }
    
    profs = menus.get(nicho, [])
    buttons = [[InlineKeyboardButton(text=p, callback_data=f"hunt_{p}")] for p in profs]
    buttons.append([InlineKeyboardButton(text="🔙 Voltar aos Nichos", callback_data="hunt_menu")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("🎯 *Selecione a Tecnologia/Profissão:*", reply_markup=markup, parse_mode="Markdown")

# ----------------- PROCESSO DE BUSCA -----------------
@dp.callback_query(F.data.startswith("hunt_") and F.data != "hunt_menu")
async def process_hunt(callback: CallbackQuery):
    keyword = callback.data.split("_", 1)[1]
    await _do_hunt(keyword, callback.message, callback=callback)

async def _do_hunt(keyword: str, message: types.Message, callback: CallbackQuery = None):
    
    active_plats = [k for k, v in user_settings["platforms"].items() if v]
    if not active_plats:
        if callback: await callback.answer("Ative pelo menos uma plataforma em Configurações!", show_alert=True)
        else: await message.answer("Ative pelo menos uma plataforma em Configurações!")
        return
        
    plats_str = ', '.join([p.replace('_', ' ').title() for p in active_plats])
    msg_text = f"⏳ *Iniciando os motores para: {keyword}*\n\nLocalização: {user_settings['location']}\nNível: {user_settings['level']}\nContrato: {user_settings['contract']}\nFormação: {user_settings['education']}\nPlataformas: {plats_str}..."
    if callback:
        await callback.message.edit_text(msg_text, parse_mode="Markdown")
    else:
        await message.answer(msg_text, parse_mode="Markdown")
    
    async def fetch_plat(plat):
        try:
            module = importlib.import_module(f"scrapers.{plat}")
            for tentativa in range(3):
                try:
                    if plat in ['jsearch', 'jooble', 'github_vagas', 'novenove', 'freelancer', 'meta_ads', 'indeed', 'linkedin', 'gmail', 'glassdoor', 'infojobs']:
                        return await asyncio.to_thread(module.scrape, keyword=keyword, level=user_settings["level"], country=user_settings["location"])
                    else:
                        return await asyncio.to_thread(module.scrape, keyword=keyword, level=user_settings["level"])
                except Exception as inner_e:
                    logger.warning(f"Instabilidade no {plat} (Tentativa {tentativa+1}/3): {inner_e}")
                    if tentativa < 2:
                        await asyncio.sleep(2)
        except Exception as e:
            logger.exception(f"Erro fatal ao carregar scraper {plat}")
        return []

    results = await asyncio.gather(*(fetch_plat(p) for p in active_plats))
    raw_jobs = []
    for r in results:
        if r:
            raw_jobs.extend(r)
            
    # ------ FILTRO DE ALTA PRECISÃO (Agora 100% via IA) ------
    all_jobs = []
    
    for job in raw_jobs:
        if "Sem vagas" in job['title'] or "Não houve" in job['requirements']:
            continue
        all_jobs.append(job)
    # -------------------------------------
    
    if not all_jobs:
        await message.answer("❌ Nenhuma vaga retornou das APIs.")
        return

    import os
    import scrapers.ai_filter as ai_filter
    
    if not user_settings["ai_filter"]:
        premium_jobs = all_jobs
        await message.answer(f"🚀 *Modo Trator Ativado!*\nEnviando todas as {len(premium_jobs)} vagas brutas sem filtro de IA...", parse_mode="Markdown")
    else:
        curriculo_path = "curriculo.txt"
        resume_text = ""
        if os.path.exists(curriculo_path):
            with open(curriculo_path, "r", encoding="utf-8") as f:
                resume_text = f.read()

        await message.answer(f"🛡️ *Escudo PT-BR Ativado!*\nLimpando vagas gringas antes de enviar para a IA...", parse_mode="Markdown")
        
        from langdetect import detect
        
        def is_brazilian_job(text):
            try:
                # Se for muito curto, deixa passar para a IA avaliar
                if len(text) < 20: return True
                return detect(text) == 'pt'
            except:
                return True
                
        # Pré-filtro brutal: Se não for PT-BR, lixo.
        vagas_br = []
        for job in all_jobs:
            if is_brazilian_job(job.get('requirements', '')):
                vagas_br.append(job)
                
        if len(vagas_br) < len(all_jobs):
            await message.answer(f"🗑️ *Limpeza concluída:* {len(all_jobs) - len(vagas_br)} vagas gringas foram deletadas!\n🧠 *Filtro IA (Groq) Ativado nas {len(vagas_br)} vagas restantes...*", parse_mode="Markdown")
        else:
            await message.answer(f"🧠 *Filtro IA (Groq) Ativado!*\nLendo {len(vagas_br)} vagas filtradas simultaneamente para cruzar com o seu currículo...", parse_mode="Markdown")

        async def process_job(job):
            match_data = await ai_filter.score_job_match(
                resume_text, 
                job, 
                target_keyword=keyword, 
                target_location=user_settings["location"], 
                target_level=user_settings["level"],
                target_education=user_settings["education"],
                target_contract=user_settings["contract"]
            )
            job['ai_aprovado'] = match_data.get('aprovado', False)
            job['ai_score'] = match_data.get('score', 0)
            job['ai_reason'] = match_data['reason']
            job['ai_reqs'] = match_data.get('reqs', 'Não informado.')
            job['ai_bonus'] = match_data.get('bonus', 'Não mencionado.')
            job['ai_benefits'] = match_data.get('benefits', 'Não informado.')
            job['ai_model'] = match_data.get('model', 'Não especificado.')
            job['ai_proposal'] = match_data.get('proposal', '')
            job['ai_salary_declared'] = match_data.get('salary_declared', False)
            job['ai_has_benefits'] = match_data.get('has_benefits', False)
            return job

        scored_jobs = await asyncio.gather(*(process_job(job) for job in vagas_br))
        
        premium_jobs = [j for j in scored_jobs if j.get('ai_aprovado', False)]
        # Ranking por score de match com o currículo (mais relevante primeiro)
        premium_jobs.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
        
        if not premium_jobs:
            await message.answer("🚷 *Groq:* O Filtro Estruturado Reprovou todas as vagas (Violação das regras). Nenhuma sobreviveu.", parse_mode="Markdown")
            return
            
        await message.answer(f"✅ *Filtro Concluído!*\n\nDe {len(raw_jobs)} vagas brutas, apenas **{len(premium_jobs)} vagas** passaram pela Guilhotina da IA. Enviando as Top 5...", parse_mode="Markdown")
        
    await asyncio.to_thread(insert_jobs, premium_jobs)
    import scrapers.auto_apply as auto_apply
    
    count = 0
    for job in premium_jobs:
        # Pular vagas sem link válido
        link = job.get('link', '')
        if not link or not link.startswith('http'):
            logger.warning(f"Vaga sem link válido ignorada: {job.get('title', 'N/A')}")
            continue

        # Tenta Auto-Apply silenciosamente
        apply_result = auto_apply.auto_apply(job)
        
        # Indicadores visuais de Salário e Benefícios
        salary_badge = "💲 Salário Declarado" if job.get('ai_salary_declared') else "❓ Salário A Combinar"
        benefits_badge = "🎁 Com Benefícios" if job.get('ai_has_benefits') else ""
        badges = f"\n{salary_badge}"
        if benefits_badge:
            badges += f" | {benefits_badge}"
        
        # Botões de ação
        buttons = [[InlineKeyboardButton(text="🎯 Aplicar para a Vaga", url=link)]]
        
        if apply_result.get("contact_email"):
            buttons.append([InlineKeyboardButton(
                text=f"📧 Enviar Currículo ({apply_result['contact_email'][:25]}...)", 
                callback_data=f"auto_apply_{count}"
            )])
        
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Sanitizar campos para evitar que caracteres especiais do Markdown do Telegram causem falha silenciosa
        def safe_md(val, default="Não informado."):
            s = str(val) if val else default
            return s.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")

        proposal_raw = job.get('ai_proposal', '')
        plat_lower = job.get('platform', '').lower()
        is_freela_plat = any(p in plat_lower for p in ['workana', 'novenove', 'freelancer'])
        has_proposal = proposal_raw and proposal_raw != 'N/A' and is_freela_plat

        text = (
            f"💎 *{safe_md(job.get('title', 'Vaga'))}*\n"
            f"🧠 *Match IA:* {job.get('ai_score', '?')}/100\n"
            f"💡 *Motivo:* {safe_md(job.get('ai_reason', ''), '')}\n"
            f"{badges}\n\n"
            f"🏢 Empresa: `{job.get('company', 'N/A')}`\n"
            f"🌐 Fonte: `{job.get('platform', 'N/A')}`\n\n"
            f"📍 *Modelo de Trabalho:*\n_{safe_md(job.get('ai_model', ''), 'Não especificado.')}_\n\n"
            f"🛠️ *Requisitos Obrigatórios:*\n_{safe_md(job.get('ai_reqs', ''), 'Não informado.')}_\n\n"
            f"💡 *Desejáveis / Diferenciais:*\n_{safe_md(job.get('ai_bonus', ''), 'Não mencionado.')}_\n\n"
            f"💰 *Salário e Benefícios:*\n_{safe_md(job.get('ai_benefits', ''), 'Não informado.')}_\n\n"
            f"📝 *Resumo Original:*\n{str(job.get('requirements', ''))[:100]}..."
        )
        
        # O Telegram tem limite de 4096 caracteres. Se passar, cortamos.
        if len(text) > 4000:
            text = text[:4000] + "... [Cortado pelo limite do Telegram]"
            
        try:
            sent_msg = await message.answer(text, reply_markup=markup, parse_mode="Markdown")
            
            # Se tiver proposta, envia como resposta à vaga (para não explodir o limite)
            if has_proposal:
                prop_text = f"🤖 *Proposta Comercial Inteligente (Clique no texto para copiar):*\n\n```\n{proposal_raw}\n```"
                if len(prop_text) > 4000:
                    prop_text = prop_text[:4000] + "\n```\n... [Cortado]"
                await sent_msg.reply(prop_text, parse_mode="Markdown")
                
            count += 1
            if count >= 10:
                break
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Erro Markdown ao enviar vaga '{job.get('title')}': {e}")
            # Fallback: enviar sem formatação para não perder a vaga
            try:
                plain = f"💎 {job.get('title','Vaga')}\n🏢 {job.get('company','')}\n🌐 {job.get('platform','')}\n🔗 {link}"
                await message.answer(plain, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎯 Aplicar", url=link)]]))
                count += 1
                if count >= 10:
                    break
            except Exception as e2:
                logger.error(f"Fallback também falhou: {e2}")
            
    if count > 0:
         await message.answer("🎉 Listagem Finalizada! Para mais vagas, inicie outra caçada.")

# ----------------- NLP: TEXTO LIVRE -----------------
@dp.message(F.text)
async def handle_free_text(message: types.Message):
    if message.text.startswith("/"):
        return
        
    await message.answer("🧠 *Processando seu pedido...* (Extraindo intenção, Localidade, Senioridade e Contrato)", parse_mode="Markdown")
    
    import scrapers.ai_filter as ai_filter
    intent = await ai_filter.extract_hunt_intent(message.text)
    
    keyword = intent.get("keyword", "Vagas")
    location = intent.get("location", "Brasil (Remoto)")
    level = intent.get("level", "Todos")
    contract = intent.get("contract", "Todos")
    education = intent.get("education", "Todos")
    
    # Atualiza as configurações do usuário de forma autônoma
    if location in ["Brasil (Remoto)", "Londrina/PR", "Assaí/PR"]:
        user_settings["location"] = location
    if level in ["Todos", "Júnior", "Pleno", "Sênior"]:
        user_settings["level"] = level
    if contract in ["Todos", "PJ", "CLT"]:
        user_settings["contract"] = contract
    if education in ["Todos", "Sem Formação"]:
        user_settings["education"] = education
        
    # Dispara os motores
    await _do_hunt(keyword, message)

@dp.message(F.document)
async def handle_document(message: types.Message, bot: Bot):
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ Por favor, envie o seu currículo em formato PDF.")
        return
        
    msg_status = await message.answer("📄 *Lendo PDF...*", parse_mode="Markdown")
    file = await bot.get_file(message.document.file_id)
    file_path = "temp_curriculo.pdf"
    await bot.download_file(file.file_path, file_path)
    
    try:
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
                text += "\n"
                
        with open("curriculo.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        await msg_status.edit_text("🧠 *Currículo Salvo!*\nEnviando para o Groq gerar a sua estratégia de busca de vagas...", parse_mode="Markdown")
        
        import scrapers.ai_filter as ai_filter
        keywords = await ai_filter.analyze_resume_for_keywords(text)
        
        buttons = [[InlineKeyboardButton(text=f"🔍 Buscar: {kw}", callback_data=f"hunt_{kw}")] for kw in keywords]
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await msg_status.edit_text(
            f"🎯 *Análise Concluída!*\n\nBaseado na leitura do seu PDF, a IA deduziu que essas são as 3 profissões de maior conversão para você no mercado remoto/B2B atual.\n\n*Clique em um botão abaixo para disparar o robô:*",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        await msg_status.edit_text(f"❌ Erro ao ler PDF: {e}")

@dp.message()
async def echo_message(message: types.Message):
    if not message.text.startswith("/"):
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Procurar Vagas", callback_data="hunt_menu")]
        ])
        await message.answer("Para iniciar as buscas, clique no botão abaixo ou digite /start", reply_markup=markup)

async def main():
    print("Bot Nativo Ligado e Aguardando Comandos!")
    await bot.set_chat_menu_button()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
