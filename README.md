# Jules Telegram Bot 🤖

Este é um bot simples do Telegram integrado com a API do Google Jules para automatizar tarefas de codificação.

## Funcionalidades

- **Início de Tarefas:** Use `/task <descrição>` para criar uma nova sessão no Jules.
- **Monitoramento em Tempo Real:** O bot informa o que está fazendo (ex: "Planning", "In Progress") e o que foi feito (ex: "Plan generated", "Code changes ready").
- **Resultados:** Ao concluir, o bot envia o link do Pull Request ou o resultado da tarefa.

## Como Usar

1. **Obtenha um Token de Bot do Telegram:**
   - Fale com o [@BotFather](https://t.me/botfather) no Telegram.
   - Crie um novo bot e copie o Token.

2. **Configure as Variáveis de Ambiente:**
   - `TELEGRAM_BOT_TOKEN`: O token do seu bot.
   - `JULES_API_KEY`: Sua chave da API do Jules (já configurada no código).

3. **Instale as Dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute o Bot:**
   ```bash
   python bot.py
   ```

## Comandos

- `/start` ou `/help`: Mostra a mensagem de boas-vindas e comandos.
- `/task <descrição>`: Inicia uma nova tarefa de codificação.
- `/status`: Verifica se o bot está online.

## Sobre o Jules

O Jules é um agente de codificação autônomo da Google que ajuda a corrigir bugs, adicionar documentação e construir novas funcionalidades diretamente no seu repositório GitHub.
