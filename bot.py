import logging
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Configurações
TELEGRAM_TOKEN = "8610767255:AAEDHuCOQDvTe7BEh8ddKc3ReAfACSSbCVo"
JULES_API_KEY = "AQ.Ab8RN6LJ9PYBWxesVc6sFW6LRKO16zOrPEGqeizFNxj_NiKO6A"
JULES_BASE_URL = "https://jules.googleapis.com/v1alpha"

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe o menu principal com botões interativos."""
    keyboard = [
        [InlineKeyboardButton("📂 Listar Repositórios", callback_data='list_sources')],
        [InlineKeyboardButton("🕒 Listar Sessões Ativas", callback_data='list_sessions')],
        [InlineKeyboardButton("➕ Criar Nova Sessão", callback_data='create_session')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🤖 **Olá! Eu sou o seu assistente para o Google Jules.**\n\n"
        "Posso ajudar você a automatizar tarefas de codificação usando a IA do Google.\n"
        "O que você gostaria de fazer agora?"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gerencia os cliques nos botões do menu."""
    query = update.callback_query
    await query.answer()

    if query.data == 'list_sources':
        await list_sources(query)
    elif query.data == 'list_sessions':
        await list_sessions(query)
    elif query.data == 'create_session':
        await query.edit_message_text("✍️ Por favor, envie a descrição da tarefa (prompt) para iniciar uma nova sessão.")
        context.user_data['awaiting_prompt'] = True
    elif query.data.startswith('sel_source_'):
        source_id = query.data.replace('sel_source_', '')
        context.user_data['selected_source'] = f"sources/{source_id}"
        await query.edit_message_text(f"✅ Repositório selecionado: `{source_id}`.\nAgora envie o prompt da tarefa.", parse_mode='Markdown')
        context.user_data['awaiting_prompt'] = True
    elif query.data.startswith('view_session_'):
        session_id = query.data.replace('view_session_', '')
        await view_session_details(query, session_id)
    elif query.data == 'main_menu':
        await start(update, context)

async def list_sources(query):
    """Lista os repositórios disponíveis na API Jules."""
    headers = {"x-goog-api-key": JULES_API_KEY}
    try:
        response = requests.get(f"{JULES_BASE_URL}/sources", headers=headers)
        if response.status_code == 200:
            sources = response.json().get('sources', [])
            if not sources:
                keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data='main_menu')]]
                await query.edit_message_text("📭 Nenhum repositório encontrado.", reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            keyboard = []
            for s in sources:
                sid = s['name'].split('/')[-1]
                keyboard.append([InlineKeyboardButton(f"📁 {sid}", callback_data=f"sel_source_{sid}")])
            
            keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data='main_menu')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("📂 **Selecione um repositório:**", reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(f"❌ Erro ao buscar repositórios: {response.status_code}")
    except Exception as e:
        await query.edit_message_text(f"❌ Erro de conexão: {str(e)}")

async def list_sessions(query):
    """Lista as sessões ativas com botões para ver detalhes."""
    headers = {"x-goog-api-key": JULES_API_KEY}
    try:
        response = requests.get(f"{JULES_BASE_URL}/sessions", headers=headers)
        if response.status_code == 200:
            sessions = response.json().get('sessions', [])
            if not sessions:
                keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data='main_menu')]]
                await query.edit_message_text("📭 Nenhuma sessão ativa encontrada.", reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            keyboard = []
            for s in sessions:
                title = s.get('title', s['id'])
                state = s['state']
                keyboard.append([InlineKeyboardButton(f"[{state}] {title}", callback_data=f"view_session_{s['id']}")])
            
            keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data='main_menu')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("🕒 **Selecione uma sessão para ver detalhes:**", reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(f"❌ Erro ao buscar sessões: {response.status_code}")
    except Exception as e:
        await query.edit_message_text(f"❌ Erro de conexão: {str(e)}")

async def view_session_details(query, session_id):
    """Mostra detalhes de uma sessão específica."""
    headers = {"x-goog-api-key": JULES_API_KEY}
    try:
        response = requests.get(f"{JULES_BASE_URL}/sessions/{session_id}", headers=headers)
        if response.status_code == 200:
            s = response.json()
            text = (
                f"🔍 **Detalhes da Sessão**\n\n"
                f"🆔 **ID:** `{s['id']}`\n"
                f"📌 **Título:** {s.get('title', 'Sem título')}\n"
                f"⚡ **Status:** `{s['state']}`\n"
                f"📝 **Prompt:** {s.get('prompt', 'N/A')}\n"
                f"📅 **Criada em:** {s['createTime']}\n"
            )
            
            keyboard = [[InlineKeyboardButton("⬅️ Voltar para Lista", callback_data='list_sessions')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(f"❌ Erro ao buscar detalhes da sessão: {response.status_code}")
    except Exception as e:
        await query.edit_message_text(f"❌ Erro de conexão: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens de texto para criar novas sessões."""
    if context.user_data.get('awaiting_prompt'):
        prompt = update.message.text
        source = context.user_data.get('selected_source')
        
        await update.message.reply_text("🚀 **Iniciando sessão no Jules... Aguarde.**", parse_mode='Markdown')
        
        headers = {
            "x-goog-api-key": JULES_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "prompt": prompt,
            "requirePlanApproval": False
        }
        if source:
            data["sourceContext"] = {"source": source}

        try:
            response = requests.post(f"{JULES_BASE_URL}/sessions", headers=headers, json=data)
            if response.status_code == 200:
                session = response.json()
                session_id = session['id']
                await update.message.reply_text(
                    f"✅ **Sessão criada!**\nID: `{session_id}`\nStatus: `{session['state']}`\n\nMonitorando progresso...",
                    parse_mode='Markdown'
                )
                
                asyncio.create_task(monitor_session(update, session_id))
            else:
                await update.message.reply_text(f"❌ Erro ao criar sessão: {response.text}")
        except Exception as e:
            await update.message.reply_text(f"❌ Erro: {str(e)}")
        
        context.user_data['awaiting_prompt'] = False

async def monitor_session(update, session_id):
    """Monitora o status da sessão e notifica o usuário."""
    headers = {"x-goog-api-key": JULES_API_KEY}
    last_state = ""
    
    while True:
        try:
            response = requests.get(f"{JULES_BASE_URL}/sessions/{session_id}", headers=headers)
            if response.status_code == 200:
                session = response.json()
                current_state = session['state']
                
                if current_state != last_state:
                    await update.message.reply_text(f"🔔 **Atualização da Sessão {session_id}**:\nStatus: `{current_state}`", parse_mode='Markdown')
                    last_state = current_state
                
                if current_state in ['COMPLETED', 'FAILED']:
                    if current_state == 'COMPLETED' and 'outputs' in session:
                        for output in session['outputs']:
                            if 'pullRequest' in output:
                                pr = output['pullRequest']
                                await update.message.reply_text(f"🎉 **Tarefa concluída!**\nPR criado: {pr['url']}", parse_mode='Markdown')
                    break
            else:
                break
        except Exception as e:
            logging.error(f"Erro no monitoramento: {e}")
        
        await asyncio.sleep(15)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot iniciado...")
    application.run_polling()
