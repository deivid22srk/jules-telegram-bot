import os
import time
import requests
import telebot
from threading import Thread

# Configurações
JULES_API_KEY = "AQ.Ab8RN6LJ9PYBWxesVc6sFW6LRKO16zOrPEGqeizFNxj_NiKO6A"
# O usuário deve fornecer o TOKEN do Telegram Bot via variável de ambiente ou editando aqui
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "SEU_TELEGRAM_BOT_TOKEN_AQUI")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

class JulesAPI:
    BASE_URL = "https://jules.googleapis.com/v1alpha"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_session(self, prompt, title=None):
        url = f"{self.BASE_URL}/sessions"
        data = {
            "prompt": prompt,
            "requirePlanApproval": False # Auto-approve para simplicidade
        }
        if title:
            data["title"] = title
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_session(self, session_name):
        url = f"{self.BASE_URL}/{session_name}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_activities(self, session_name, last_activity_id=None):
        url = f"{self.BASE_URL}/{session_name}/activities"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        activities = response.json().get("activities", [])
        
        if last_activity_id:
            # Retorna apenas novas atividades
            new_activities = []
            found_last = False
            for act in reversed(activities):
                if act["id"] == last_activity_id:
                    found_last = True
                    break
                new_activities.append(act)
            return list(reversed(new_activities))
        
        return activities

jules = JulesAPI(JULES_API_KEY)

def monitor_session(chat_id, session_name):
    last_activity_id = None
    last_state = None
    
    bot.send_message(chat_id, f"🚀 Sessão iniciada: {session_name}\nMonitorando progresso...")

    while True:
        try:
            # Verificar estado da sessão
            session = jules.get_session(session_name)
            current_state = session.get("state")
            
            if current_state != last_state:
                bot.send_message(chat_id, f"🔄 Status alterado para: *{current_state}*", parse_mode="Markdown")
                last_state = current_state

            # Verificar novas atividades
            new_activities = jules.list_activities(session_name, last_activity_id)
            for act in new_activities:
                desc = act.get("description", "Nova atividade")
                bot.send_message(chat_id, f"📝 *Atividade:* {desc}", parse_mode="Markdown")
                last_activity_id = act["id"]

            if current_state in ["COMPLETED", "FAILED"]:
                if current_state == "COMPLETED":
                    outputs = session.get("outputs", [])
                    msg = "✅ *Tarefa concluída com sucesso!*"
                    if outputs:
                        msg += "\n\nResultados:"
                        for out in outputs:
                            if "pullRequest" in out:
                                msg += f"\n- PR: {out['pullRequest']['url']}"
                    bot.send_message(chat_id, msg, parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, "❌ *A tarefa falhou.* Verifique os logs no console do Jules.", parse_mode="Markdown")
                break

            time.sleep(10) # Polling a cada 10 segundos
        except Exception as e:
            print(f"Erro ao monitorar: {e}")
            time.sleep(10)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "Olá! Eu sou o Bot do Jules. 🤖\n\n"
        "Posso ajudar você a automatizar tarefas de codificação usando a IA do Google Jules.\n\n"
        "Comandos:\n"
        "/task <descrição> - Inicia uma nova tarefa no Jules\n"
        "/status - Mostra informações básicas"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['task'])
def handle_task(message):
    prompt = message.text.replace('/task', '').strip()
    if not prompt:
        bot.reply_to(message, "Por favor, forneça uma descrição para a tarefa. Ex: `/task Adicione testes unitários ao módulo X`", parse_mode="Markdown")
        return

    try:
        session = jules.create_session(prompt)
        session_name = session["name"]
        
        # Iniciar monitoramento em uma thread separada
        Thread(target=monitor_session, args=(message.chat.id, session_name)).start()
        
    except Exception as e:
        bot.reply_to(message, f"Erro ao criar sessão: {str(e)}")

@bot.message_handler(commands=['status'])
def handle_status(message):
    bot.reply_to(message, "Estou online e pronto para receber tarefas! Use /task para começar.")

if __name__ == "__main__":
    print("Bot iniciado...")
    bot.infinity_polling()
