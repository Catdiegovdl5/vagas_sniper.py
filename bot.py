import asyncio
import importlib
import PyPDF2
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import sys
sys.path.append(".")
from database import insert_jobs, init_db
init_db()  # Garante que as tabelas existem quando o bot inicia
import os
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7724330024:AAFtoSLgXVDlvNmeyPCVMnkWIqbk4wvLSVg")

import traceback
from loguru import logger

# --- Configurando o Monitoramento Profissional (Loguru) ---
logger.remove() # Remove o handler padrão
logger.add(sys.stderr, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="DEBUG")
logger.add("erros_robo.log", rotation="10 MB", retention="5 days", level="DEBUG", 
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

import copy

DEFAULT_RESUME = """
Diego Santos | Especialista Digital Full-Stack

🎯 Áreas de Atuação:
- Gestão de Tráfego Pago: Meta Ads (Facebook/Instagram), Google Ads, TikTok Ads, lojistas, infoprodutos e lançamentos digitais.
- Edição de Vídeo & Motion: Premiere Pro, CapCut Pro, After Effects. Especialista em retenção e viralização (524k+ views orgânicos).
- Criação de Conteúdo / Social Media: Reels, TikTok, YouTube Shorts, copy para posts e campanhas.
- Automação com IA e Python: scripts de automação, bots do Telegram, pipelines de vídeo na nuvem, integrações com APIs de IA (Groq, OpenAI).
- Desenvolvimento Web: HTML, CSS, JavaScript, sites de portfólio, landing pages de alta conversão.

💼 Cases e Resultados:
- 524.000+ views orgânicos em um único Reels (Instagram).
- 56.600+ views no TikTok em nicho Geek/Anime.
- 370 vídeos publicados no YouTube com identidade visual consistente.
- Pipeline automatizada de corte e montagem de vídeos com Python.
- Desenvolvimento de bot inteligente de captura de vagas com IA (Groq) e Telegram.

🛠️ Ferramentas: Meta Business Suite, Google Ads Manager, Premiere Pro, CapCut, After Effects, Python, Playwright, GitHub, Render, n8n.
"""

DEFAULT_SETTINGS = {
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

user_settings_db = {}

def get_user_settings(chat_id):
    chat_id = str(chat_id)
    if chat_id not in user_settings_db:
        user_settings_db[chat_id] = copy.deepcopy(DEFAULT_SETTINGS)
    return user_settings_db[chat_id]

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await show_main_menu(message)

@dp.message(Command("logs"))
async def cmd_logs(message: types.Message):
    if not os.path.exists("erros_robo.log"):
        await message.answer("Nenhum log de erro encontrado.")
        return
    
    with open("erros_robo.log", "r", encoding="utf-8") as f:
        # Lemos o arquivo todo e pegamos os últimos 3500 caracteres (limite do Telegram)
        lines = f.readlines()
        tail = "".join(lines[-50:])
        if len(tail) > 3500:
            tail = "..." + tail[-3500:]
            
    await message.answer(f"📜 *Últimos Logs (erros_robo.log):*\n\n```log\n{tail}\n```", parse_mode="Markdown")

@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    await callback.answer()
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
    await callback.answer()
    chat_id = callback.message.chat.id
    await callback.message.edit_text("⚙️ *Configurações do Robô*", reply_markup=get_settings_markup(chat_id), parse_mode="Markdown")

def get_settings_markup(chat_id):
    settings = get_user_settings(chat_id)
    p = settings["platforms"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📍 Local: {settings['location']} (Mudar)", callback_data="change_location")],
        [InlineKeyboardButton(text=f"Nível: {settings['level']} (Mudar)", callback_data="change_level")],
        [InlineKeyboardButton(text=f"Contrato: {settings['contract']} (Mudar)", callback_data="change_contract")],
        [InlineKeyboardButton(text=f"Formação: {settings['education']} (Mudar)", callback_data="change_education")],
        [InlineKeyboardButton(text=f"👨‍💻 Modo Exclusivo Freelancer: {'✅ ON' if settings.get('modo_freelancer', False) else '❌ OFF'}", callback_data="toggle_modo_freelancer")],
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
        [InlineKeyboardButton(text=f"🧠 Filtro IA (Groq): {'✅ ON' if settings['ai_filter'] else '❌ OFF'}", callback_data="toggle_ai")],
        [InlineKeyboardButton(text="🔙 Voltar ao Início", callback_data="main_menu")]
    ])

@dp.callback_query(F.data == "change_level")
async def change_level(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.message.chat.id
    settings = get_user_settings(chat_id)
    levels = ["Todos", "Júnior", "Pleno", "Sênior"]
    idx = levels.index(settings["level"])
    settings["level"] = levels[(idx + 1) % len(levels)]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup(chat_id))

@dp.callback_query(F.data == "change_location")
async def change_location(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.message.chat.id
    settings = get_user_settings(chat_id)
    locations = ["Brasil (Remoto)", "Londrina/PR", "Assaí/PR"]
    idx = locations.index(settings["location"])
    settings["location"] = locations[(idx + 1) % len(locations)]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup(chat_id))

@dp.callback_query(F.data == "change_contract")
async def change_contract(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.message.chat.id
    settings = get_user_settings(chat_id)
    contracts = ["Todos", "PJ", "CLT", "Freelancer"]
    idx = contracts.index(settings["contract"])
    settings["contract"] = contracts[(idx + 1) % len(contracts)]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup(chat_id))

@dp.callback_query(F.data == "change_education")
async def change_education(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.message.chat.id
    settings = get_user_settings(chat_id)
    educations = ["Todos", "Sem Formação"]
    idx = educations.index(settings["education"])
    settings["education"] = educations[(idx + 1) % len(educations)]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup(chat_id))

@dp.callback_query(F.data == "toggle_ai")
async def toggle_ai(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.message.chat.id
    settings = get_user_settings(chat_id)
    settings["ai_filter"] = not settings["ai_filter"]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup(chat_id))

@dp.callback_query(F.data == "toggle_modo_freelancer")
async def toggle_modo_freelancer(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.message.chat.id
    settings = get_user_settings(chat_id)
    is_now_on = not settings.get("modo_freelancer", False)
    settings["modo_freelancer"] = is_now_on
    
    freelance_plats = ["workana", "novenove", "freelancer"]
    clt_plats = ["jsearch", "jooble", "remotar", "github_vagas", "meta_ads", "indeed", "linkedin", "glassdoor", "infojobs"]
    
    if is_now_on:
        for p in freelance_plats: settings["platforms"][p] = True
        for p in clt_plats: settings["platforms"][p] = False
        settings["contract"] = "Freelancer"
    else:
        for p in freelance_plats: settings["platforms"][p] = False
        for p in clt_plats: settings["platforms"][p] = True
        settings["contract"] = "Todos"
        
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup(chat_id))

@dp.callback_query(F.data.startswith("toggle_"))
async def toggle_platform(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.message.chat.id
    settings = get_user_settings(chat_id)
    plat = callback.data.replace("toggle_", "")
    if plat in settings["platforms"]:
        settings["platforms"][plat] = not settings["platforms"][plat]
    await callback.message.edit_reply_markup(reply_markup=get_settings_markup(chat_id))

# ----------------- CAÇAR VAGAS (NICHOS) -----------------
@dp.callback_query(F.data == "hunt_menu")
async def hunt_menu(callback: CallbackQuery):
    await callback.answer()
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
    await callback.answer()
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
    chat_id = callback.message.chat.id
    settings = get_user_settings(chat_id)
    active_plats = [k for k, v in settings["platforms"].items() if v]
    if not active_plats:
        try:
            await callback.answer("Ative pelo menos uma plataforma em Configurações!", show_alert=True)
        except Exception:
            await callback.message.answer("Ative pelo menos uma plataforma em Configurações!")
        return
        
    await callback.answer()
    keyword = callback.data.split("_", 1)[1]
    await _do_hunt(keyword, callback.message, callback=callback)

async def _do_hunt(keyword: str, message: types.Message, callback: CallbackQuery = None):
    chat_id = message.chat.id
    settings = get_user_settings(chat_id)
    active_plats = [k for k, v in settings["platforms"].items() if v]
    if not active_plats:
        if callback:
            try:
                await callback.answer("Ative pelo menos uma plataforma em Configurações!", show_alert=True)
                return
            except Exception:
                pass
        await message.answer("Ative pelo menos uma plataforma em Configurações!")
        return
        
    plats_str = ', '.join([p.replace('_', ' ').title() for p in active_plats])
    msg_text = f"⏳ *Iniciando os motores para: {keyword}*\n\nLocalização: {settings['location']}\nNível: {settings['level']}\nContrato: {settings['contract']}\nFormação: {settings['education']}\nPlataformas: {plats_str}..."
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
                        return await asyncio.to_thread(module.scrape, keyword=keyword, level=settings["level"], country=settings["location"])
                    else:
                        return await asyncio.to_thread(module.scrape, keyword=keyword, level=settings["level"])
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

    import scrapers.ai_filter as ai_filter
    
    await message.answer(f"🛡️ *Escudo PT-BR Ativado!*\nLimpando vagas gringas antes do processamento final...", parse_mode="Markdown")
    from langdetect import detect
    
    def is_brazilian_job(text):
        try:
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
        await message.answer(f"🗑️ *Limpeza concluída:* {len(all_jobs) - len(vagas_br)} vagas gringas foram deletadas!", parse_mode="Markdown")
        
    # --- NOVO MODELO: Enviar TODAS as vagas BR. IA usada APENAS para gerar proposta em freelance ---
    premium_jobs = vagas_br
    await message.answer(f"🚀 *{len(premium_jobs)} vagas encontradas!* Gerando propostas para Workana/99Freelas e enviando...", parse_mode="Markdown")

    import scrapers.ai_filter as ai_filter

    async def generate_proposal_only(job):
        """Usa a IA apenas para gerar proposta em vagas de plataformas freelance."""
        plat_lower = job.get('platform', '').lower()
        is_freela_plat = any(p in plat_lower for p in ['workana', '99freelas', 'freelancer'])
        if is_freela_plat:
            match_data = await ai_filter.score_job_match(
                DEFAULT_RESUME, job,
                target_keyword=keyword,
                target_location=settings["location"],
                target_level=settings["level"],
                target_education=settings["education"],
                target_contract=settings["contract"]
            )
            job['ai_proposal'] = match_data.get('proposal', '')
        else:
            job['ai_proposal'] = ''
        return job

    # Gera propostas em paralelo (só para freelance)
    premium_jobs = await asyncio.gather(*(generate_proposal_only(j) for j in premium_jobs))
        
    await asyncio.to_thread(insert_jobs, premium_jobs)
    import auto_apply
    
    count = 0

    async def send_with_retry(coro_fn, max_retries=3):
        """Executa uma função de envio com retry automático em caso de queda de conexão."""
        from aiohttp import ClientError
        for attempt in range(max_retries):
            try:
                return await coro_fn()
            except (ClientError, Exception) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Backoff exponencial: 1s, 2s, 4s
                    logger.warning(f"Falha de envio (tentativa {attempt+1}/{max_retries}): {e}. Aguardando {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Envio falhou após {max_retries} tentativas: {e}")
                    raise

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
        is_freela_plat = any(p in plat_lower for p in ['workana', '99freelas', 'freelancer'])
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
            sent_msg = await send_with_retry(lambda: message.answer(text, reply_markup=markup, parse_mode="Markdown"))
            
            # Se tiver proposta, envia como resposta à vaga (para não explodir o limite)
            if has_proposal:
                prop_text = f"🤖 *Proposta Comercial Inteligente (Clique no texto para copiar):*\n\n```\n{proposal_raw}\n```"
                if len(prop_text) > 4000:
                    prop_text = prop_text[:4000] + "\n```\n... [Cortado]"
                await send_with_retry(lambda: sent_msg.reply(prop_text, parse_mode="Markdown"))
                
            count += 1
            await asyncio.sleep(1.2)  # 1.2s entre mensagens para evitar rate limit do Telegram
        except Exception as e:
            logger.error(f"Erro Markdown ao enviar vaga '{job.get('title')}': {e}")
            # Fallback: enviar sem formatação para não perder a vaga
            try:
                plain = f"💎 {job.get('title','Vaga')}\n🏢 {job.get('company','')}\n🌐 {job.get('platform','')}\n🔗 {link}"
                await send_with_retry(lambda: message.answer(plain, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎯 Aplicar", url=link)]])))
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
    
    chat_id = message.chat.id
    settings = get_user_settings(chat_id)
    
    # Atualiza as configurações do usuário de forma autônoma
    if location in ["Brasil (Remoto)", "Londrina/PR", "Assaí/PR"]:
        settings["location"] = location
    if level in ["Todos", "Júnior", "Pleno", "Sênior"]:
        settings["level"] = level
    if contract in ["Todos", "PJ", "CLT"]:
        settings["contract"] = contract
    if education in ["Todos", "Sem Formação"]:
        settings["education"] = education
        
    # Dispara os motores
    await _do_hunt(keyword, message)

@dp.message(F.document)
async def handle_document(message: types.Message, bot: Bot):
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ Por favor, envie o seu currículo em formato PDF.")
        return
        
    msg_status = await message.answer("📄 *Lendo PDF...*", parse_mode="Markdown")
    file = await bot.get_file(message.document.file_id)
    user_id = message.chat.id
    file_path = f"temp_curriculo_{user_id}.pdf"
    await bot.download_file(file.file_path, file_path)
    
    try:
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
                text += "\n"
                
        curriculo_txt_path = f"curriculo_{user_id}.txt"
        with open(curriculo_txt_path, "w", encoding="utf-8") as f:
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
