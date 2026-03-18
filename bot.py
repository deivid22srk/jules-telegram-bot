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
    keyboard = [
        [InlineKeyboardButton("Listar Repositórios", callback_data='list_sources')],
        [InlineKeyboardButton("Listar Sessões Ativas", callback_data='list_sessions')],
        [InlineKeyboardButton("Criar Nova Sessão", callback_data='create_session')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Olá! Eu sou o seu assistente para o Google Jules.\n"
        "O que você gostaria de fazer hoje?",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'list_sources':
        await list_sources(query)
    elif query.data == 'list_sessions':
        await list_sessions(query)
    elif query.data == 'create_session':
        await query.edit_message_text("Por favor, envie a descrição da tarefa (prompt) para iniciar uma nova sessão.")
        context.user_data['awaiting_prompt'] = True
    elif query.data.startswith('sel_source_'):
        source_id = query.data.replace('sel_source_', '')
        context.user_data['selected_source'] = f"sources/{source_id}"
        await query.edit_message_text(f"Repositório selecionado: {source_id}. Agora envie o prompt da tarefa.")
        context.user_data['awaiting_prompt'] = True

async def list_sources(query):
    headers = {"x-goog-api-key": JULES_API_KEY}
    try:
        response = requests.get(f"{JULES_BASE_URL}/sources", headers=headers)
        if response.status_code == 200:
            sources = response.json().get('sources', [])
            if not sources:
                await query.edit_message_text("Nenhum repositório encontrado.")
                return
            
            keyboard = []
            for s in sources:
                # O nome vem como "sources/id"
                sid = s['name'].split('/')[-1]
                keyboard.append([InlineKeyboardButton(sid, callback_data=f"sel_source_{sid}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Selecione um repositório:", reply_markup=reply_markup)
        else:
            await query.edit_message_text(f"Erro ao buscar repositórios: {response.status_code}")
    except Exception as e:
        await query.edit_message_text(f"Erro de conexão: {str(e)}")

async def list_sessions(query):
    headers = {"x-goog-api-key": JULES_API_KEY}
    try:
        response = requests.get(f"{JULES_BASE_URL}/sessions", headers=headers)
        if response.status_code == 200:
            sessions = response.json().get('sessions', [])
            if not sessions:
                await query.edit_message_text("Nenhuma sessão ativa encontrada.")
                return
            
            text = "Sessões Recentes:\n\n"
            for s in sessions:
                text += f"ID: {s['id']}\nTítulo: {s.get('title', 'Sem título')}\nStatus: {s['state']}\n---\n"
            
            await query.edit_message_text(text)
        else:
            await query.edit_message_text(f"Erro ao buscar sessões: {response.status_code}")
    except Exception as e:
        await query.edit_message_text(f"Erro de conexão: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_prompt'):
        prompt = update.message.text
        source = context.user_data.get('selected_source')
        
        await update.message.reply_text("Iniciando sessão no Jules... Aguarde.")
        
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
                await update.message.reply_text(f"Sessão criada! ID: {session_id}\nStatus: {session['state']}\nMonitorando progresso...")
                
                # Iniciar monitoramento em background
                asyncio.create_task(monitor_session(update, session_id))
            else:
                await update.message.reply_text(f"Erro ao criar sessão: {response.text}")
        except Exception as e:
            await update.message.reply_text(f"Erro: {str(e)}")
        
        context.user_data['awaiting_prompt'] = False

async def monitor_session(update, session_id):
    headers = {"x-goog-api-key": JULES_API_KEY}
    last_state = ""
    
    while True:
        try:
            response = requests.get(f"{JULES_BASE_URL}/sessions/{session_id}", headers=headers)
            if response.status_code == 200:
                session = response.json()
                current_state = session['state']
                
                if current_state != last_state:
                    await update.message.reply_text(f"Atualização da Sessão {session_id}:\nStatus: {current_state}")
                    last_state = current_state
                
                if current_state in ['COMPLETED', 'FAILED']:
                    if current_state == 'COMPLETED' and 'outputs' in session:
                        for output in session['outputs']:
                            if 'pullRequest' in output:
                                pr = output['pullRequest']
                                await update.message.reply_text(f"Tarefa concluída! PR criado: {pr['url']}")
                    break
            else:
                await update.message.reply_text(f"Erro ao monitorar sessão {session_id}")
                break
        except Exception as e:
            logging.error(f"Erro no monitoramento: {e}")
        
        await asyncio.sleep(10) # Verificar a cada 10 segundos

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot iniciado...")
    application.run_polling()
