# Jules Telegram Bot

Este é um bot simples e fácil de usar para interagir com a API Jules da Google. Ele permite que você gerencie sessões de codificação diretamente pelo Telegram, recebendo notificações em tempo real sobre o progresso das tarefas.

## Funcionalidades

- **Listar Repositórios**: Visualize os repositórios conectados à sua conta Jules.
- **Listar Sessões**: Veja o status das suas sessões de codificação recentes.
- **Criar Sessão**: Inicie uma nova tarefa no Jules enviando apenas um prompt de texto.
- **Notificações em Tempo Real**: O bot monitora o progresso da sessão e avisa quando o status muda (ex: de `PLANNING` para `IN_PROGRESS` ou `COMPLETED`).
- **Integração com GitHub**: Receba links para Pull Requests criados pelo Jules diretamente no chat.

## Como Usar

1. Clone este repositório.
2. Instale as dependências:
   ```bash
   pip install python-telegram-bot requests
   ```
3. Configure suas chaves de API no arquivo `bot.py` (ou use variáveis de ambiente para maior segurança).
4. Execute o bot:
   ```bash
   python bot.py
   ```
5. No Telegram, envie `/start` para o seu bot.

## Tecnologias Utilizadas

- [Python](https://www.python.org/)
- [python-telegram-bot](https://python-telegram-bot.org/)
- [Google Jules API](https://jules.google/docs/api/reference/)
- [GitHub API](https://docs.github.com/en/rest)
