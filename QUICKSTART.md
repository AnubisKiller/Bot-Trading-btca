# Quick Start - Deploy em 5 Minutos

## 1. Obter API Keys (Testnet)

1. Acesse: https://testnet.binance.vision/
2. Faça login com GitHub
3. Gere API Key + Secret
4. Copie e guarde em local seguro

## 2. Criar Bot Telegram

1. No Telegram, fale com [@BotFather](https://t.me/botfather)
2. Envie `/newbot`
3. Escolha nome e username
4. Copie o **token** fornecido
5. Inicie conversa com seu bot (envie `/start`)
6. Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
7. Copie o **chat_id** do JSON

## 3. Deploy no Railway

### Via Interface Web:

1. Acesse https://railway.app
2. Login com GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Selecione o repositório do bot
5. Aguarde o build inicial

### Configurar Variáveis:

Clique em "Variables" e adicione:

```
MODE=TESTNET
API_KEY_BINANCE_TESTNET=sua_chave_aqui
API_SECRET_BINANCE_TESTNET=seu_secret_aqui
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
TELEGRAM_ENABLED=true
ENABLE_TRADING=true
EMERGENCY_STOP=false
REFRESH_INTERVAL=60
```

Clique em "Redeploy" após adicionar as variáveis.

## 4. Verificar

Acesse a URL fornecida pelo Railway:
```
https://seu-app.railway.app/
```

Deve retornar:
```json
{
  "status": "running",
  "timestamp": "...",
  "bot_active": true
}
```

## 5. Monitorar

- **Logs:** Painel do Railway → Deployments → Ver logs
- **Telegram:** Receberá notificações do bot
- **Status:** Acesse `/status` na URL do Railway

## Pronto! 🚀

O bot está rodando 24/7 no Railway.

## Comandos Úteis

**Parar o bot (emergência):**
```
Adicione variável: EMERGENCY_STOP=true
```

**Aumentar intervalo (economizar recursos):**
```
Altere variável: REFRESH_INTERVAL=120
```

**Ver status detalhado:**
```bash
curl https://seu-app.railway.app/status
```

## Próximos Passos

1. ✅ Monitore por 24h no Testnet
2. ✅ Verifique notificações do Telegram
3. ✅ Analise os logs para entender o comportamento
4. ✅ Ajuste parâmetros se necessário
5. ⚠️ Só migre para SPOT após validação completa

## Troubleshooting Rápido

**Bot não inicia:**
- Verifique se todas as variáveis estão configuradas
- Veja os logs no Railway para erro específico

**Não recebe notificações:**
- Certifique-se de ter iniciado conversa com o bot
- Verifique se o chat_id está correto

**Consome muita CPU:**
- Aumente REFRESH_INTERVAL para 120 ou 180

**Bot não executa trades:**
- Verifique ENABLE_TRADING=true
- Verifique EMERGENCY_STOP=false
- Veja logs para entender por que sinais são rejeitados
