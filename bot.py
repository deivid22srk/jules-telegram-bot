import logging
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

# Configurações
TELEGRAM_TOKEN = "8610767255:AAEDHuCOQDvTe7BEh8ddKc3ReAfACSSbCVo"
JULES_API_KEY = "AQ.Ab8RN6LJ9PYBWxesVc6sFW6LRKO16zOrPEGqeizFNxj_NiKO6A"
JULES_BASE_URL = "https://jules.googleapis.com/v1alpha"

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def delete_previous_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Apaga a mensagem anterior para manter o chat limpo."""
    if update.callback_query:
        try:
            await context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id
            )
        except Exception as e:
            logging.warning(f"Não foi possível apagar a mensagem: {e}")

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
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gerencia os cliques nos botões do menu."""
    query = update.callback_query
    await query.answer()

    if query.data == 'list_sources':
        await delete_previous_message(update, context)
        await list_sources(query)
    elif query.data == 'list_sessions':
        await delete_previous_message(update, context)
        await list_sessions(query)
    elif query.data == 'create_session':
        await delete_previous_message(update, context)
        await query.message.reply_text("✍️ Por favor, envie a descrição da tarefa (prompt) para iniciar uma nova sessão.")
        context.user_data['awaiting_prompt'] = True
    elif query.data.startswith('sel_source_'):
        await delete_previous_message(update, context)
        source_id = query.data.replace('sel_source_', '')
        context.user_data['selected_source'] = f"sources/{source_id}"
        await query.message.reply_text(f"✅ Repositório selecionado: `{source_id}`.\nAgora envie o prompt da tarefa.", parse_mode='Markdown')
        context.user_data['awaiting_prompt'] = True
    elif query.data.startswith('view_session_'):
        await delete_previous_message(update, context)
        session_id = query.data.replace('view_session_', '')
        await view_session_details(query, session_id)
    elif query.data.startswith('reply_session_'):
        await delete_previous_message(update, context)
        session_id = query.data.replace('reply_session_', '')
        context.user_data['replying_to_session'] = session_id
        await query.message.reply_text(f"💬 **Enviando resposta para a sessão `{session_id}`**\n\nPor favor, digite sua mensagem abaixo:", parse_mode='Markdown')
    elif query.data == 'main_menu':
        await delete_previous_message(update, context)
        await start(update, context)

async def list_sources(query):
    """Lista os repositórios disponíveis na API Jules."""
    headers = {"x-goog-api-key": JULES_API_KEY}
    try:
        response = requests.get(f"{JULES_BASE_URL}/sources", headers=headers, timeout=30)
        if response.status_code == 200:
            sources = response.json().get('sources', [])
            keyboard = []
            if not sources:
                text = "📭 Nenhum repositório encontrado."
            else:
                text = "📂 **Selecione um repositório:**"
                for s in sources:
                    sid = s['name'].split('/')[-1]
                    keyboard.append([InlineKeyboardButton(f"📁 {sid}", callback_data=f"sel_source_{sid}")])
            
            keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data='main_menu')])
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await query.message.reply_text(f"❌ Erro ao buscar repositórios: {response.status_code}")
    except Exception as e:
        await query.message.reply_text(f"❌ Erro de conexão: {str(e)}")

async def list_sessions(query):
    """Lista as sessões ativas com botões para ver detalhes."""
    headers = {"x-goog-api-key": JULES_API_KEY}
    try:
        response = requests.get(f"{JULES_BASE_URL}/sessions", headers=headers, timeout=30)
        if response.status_code == 200:
            sessions = response.json().get('sessions', [])
            keyboard = []
            if not sessions:
                text = "📭 Nenhuma sessão ativa encontrada."
            else:
                text = "🕒 **Selecione uma sessão para ver detalhes:**"
                for s in sessions:
                    title = s.get('title', s['id'])
                    state = s['state']
                    keyboard.append([InlineKeyboardButton(f"[{state}] {title}", callback_data=f"view_session_{s['id']}")])
            
            keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data='main_menu')])
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await query.message.reply_text(f"❌ Erro ao buscar sessões: {response.status_code}")
    except Exception as e:
        await query.message.reply_text(f"❌ Erro de conexão: {str(e)}")

async def view_session_details(query, session_id):
    """Mostra detalhes de uma sessão específica."""
    headers = {"x-goog-api-key": JULES_API_KEY}
    try:
        response = requests.get(f"{JULES_BASE_URL}/sessions/{session_id}", headers=headers, timeout=30)
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
            
            keyboard = []
            if s['state'] in ['AWAITING_USER_FEEDBACK', 'AWAITING_PLAN_APPROVAL', 'IN_PROGRESS']:
                keyboard.append([InlineKeyboardButton("💬 Responder ao Jules", callback_data=f"reply_session_{s['id']}")])
            
            keyboard.append([InlineKeyboardButton("⬅️ Voltar para Lista", callback_data='list_sessions')])
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            
            # Iniciar monitoramento automático ao entrar nos detalhes da sessão
            asyncio.create_task(monitor_session(query, session_id))
        else:
            await query.message.reply_text(f"❌ Erro ao buscar detalhes da sessão: {response.status_code}")
    except Exception as e:
        await query.message.reply_text(f"❌ Erro de conexão: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens de texto para criar novas sessões ou responder a sessões existentes."""
    if context.user_data.get('awaiting_prompt'):
        prompt = update.message.text
        source = context.user_data.get('selected_source')
        await update.message.reply_text("🚀 **Iniciando sessão no Jules... Aguarde.**", parse_mode='Markdown')
        
        headers = {"x-goog-api-key": JULES_API_KEY, "Content-Type": "application/json"}
        data = {"prompt": prompt, "requirePlanApproval": False}
        if source:
            data["sourceContext"] = {"source": source}

        try:
            response = requests.post(f"{JULES_BASE_URL}/sessions", headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                session = response.json()
                session_id = session['id']
                await update.message.reply_text(f"✅ **Sessão criada!**\nID: `{session_id}`\nStatus: `{session['state']}`\n\nMonitorando progresso...", parse_mode='Markdown')
                asyncio.create_task(monitor_session(update, session_id))
            else:
                await update.message.reply_text(f"❌ Erro ao criar sessão: {response.text}")
        except Exception as e:
            await update.message.reply_text(f"❌ Erro: {str(e)}")
        
        context.user_data['awaiting_prompt'] = False

    elif context.user_data.get('replying_to_session'):
        session_id = context.user_data.get('replying_to_session')
        message_text = update.message.text
        await update.message.reply_text(f"📤 **Enviando sua mensagem para a sessão `{session_id}`...**", parse_mode='Markdown')
        
        headers = {"x-goog-api-key": JULES_API_KEY, "Content-Type": "application/json"}
        data = {"prompt": message_text}

        try:
            response = requests.post(f"{JULES_BASE_URL}/sessions/{session_id}:sendMessage", headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                await update.message.reply_text(f"✅ **Mensagem enviada com sucesso!**\nO Jules continuará o trabalho agora.", parse_mode='Markdown')
                asyncio.create_task(monitor_session(update, session_id))
            else:
                await update.message.reply_text(f"❌ Erro ao enviar mensagem: {response.text}")
        except Exception as e:
            await update.message.reply_text(f"❌ Erro: {str(e)}")
        
        context.user_data['replying_to_session'] = None

async def monitor_session(update_or_query, session_id):
    """Monitora o status e as atividades detalhadas da sessão em tempo real."""
    headers = {"x-goog-api-key": JULES_API_KEY}
    last_state = ""
    processed_activities = set()
    
    # Determinar como enviar mensagens (Update ou CallbackQuery)
    if hasattr(update_or_query, 'message'):
        sender = update_or_query.message
    else:
        sender = update_or_query

    while True:
        try:
            # 1. Verificar Status da Sessão
            session_resp = requests.get(f"{JULES_BASE_URL}/sessions/{session_id}", headers=headers, timeout=30)
            if session_resp.status_code == 200:
                session = session_resp.json()
                current_state = session['state']
                
                if current_state != last_state:
                    await sender.reply_text(f"🔔 **Status da Sessão {session_id}**: `{current_state}`", parse_mode='Markdown')
                    last_state = current_state
                
                # 2. Verificar Atividades Detalhadas
                activities_resp = requests.get(f"{JULES_BASE_URL}/sessions/{session_id}/activities", headers=headers, timeout=30)
                if activities_resp.status_code == 200:
                    activities = activities_resp.json().get('activities', [])
                    for act in activities:
                        act_id = act['name']
                        if act_id not in processed_activities:
                            act_type = act.get('type', 'UNKNOWN')
                            msg = ""
                            
                            # Mapeamento detalhado de atividades
                            if act_type == 'PLAN_GENERATION':
                                msg = "🧠 **Jules está pensando e criando um plano...**"
                            elif act_type == 'RESEARCH':
                                msg = "🔍 **Jules está pesquisando no seu código...**"
                            elif act_type == 'EDIT':
                                msg = "✍️ **Jules está editando arquivos...**"
                            elif act_type == 'MESSAGE':
                                # Capturar mensagens do Jules
                                content = act.get('message', {}).get('content', '')
                                if content:
                                    msg = f"💬 **Jules respondeu:**\n\n{content}"
                            elif act_type == 'PLAN_APPROVAL_REQUEST':
                                msg = "📋 **Jules criou um plano e está aguardando sua aprovação.**"
                            
                            if msg:
                                await sender.reply_text(msg, parse_mode='Markdown')
                            processed_activities.add(act_id)

                if current_state in ['COMPLETED', 'FAILED']:
                    if current_state == 'COMPLETED' and 'outputs' in session:
                        for output in session['outputs']:
                            if 'pullRequest' in output:
                                pr = output['pullRequest']
                                await sender.reply_text(f"🎉 **Tarefa concluída!**\nPR criado: {pr['url']}", parse_mode='Markdown')
                    break
            else:
                break
        except Exception as e:
            logging.error(f"Erro no monitoramento: {e}")
        
        await asyncio.sleep(5) # Reduzi para 5 segundos para ser mais "tempo real"

if __name__ == '__main__':
    t_request = HTTPXRequest(connect_timeout=20, read_timeout=20)
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).request(t_request).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot iniciado...")
    application.run_polling()
