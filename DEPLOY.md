# Guia de Deploy no Railway

## Passo a Passo Completo

### 1. Preparar o Código

Certifique-se de que todos os arquivos estão no repositório:
- `main.py`
- `trader.py`
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `src/` (diretório completo)
- `.env.example` (apenas exemplo, não o .env real)

### 2. Criar Conta no Railway

1. Acesse https://railway.app
2. Faça login com GitHub
3. Clique em "New Project"

### 3. Deploy do Projeto

**Opção A: Deploy via GitHub**
1. Conecte seu repositório GitHub
2. Selecione o repositório do bot
3. Railway detectará automaticamente o Python

**Opção B: Deploy via CLI**
```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Inicializar projeto
railway init

# Deploy
railway up
```

### 4. Configurar Variáveis de Ambiente

No painel do Railway, vá em "Variables" e adicione:

```env
# Modo de operação
MODE=TESTNET

# API Binance Testnet
API_KEY_BINANCE_TESTNET=sua_chave_aqui
API_SECRET_BINANCE_TESTNET=seu_secret_aqui

# Telegram
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
TELEGRAM_ENABLED=true

# Trading (opcional - já tem padrões)
SYMBOL=BTCUSDT
DAILY_TARGET=0.0003
MAX_RISK_PER_TRADE=0.01
STOP_LOSS_PERCENT=0.002
TAKE_PROFIT_PERCENT=0.003
REFRESH_INTERVAL=60

# Sistema
LOG_LEVEL=INFO
ENABLE_TRADING=true
EMERGENCY_STOP=false
```

### 5. Verificar Deploy

Após o deploy, Railway fornecerá uma URL. Acesse:

```
https://seu-app.railway.app/
```

Resposta esperada:
```json
{
  "status": "running",
  "timestamp": "2026-02-02T12:00:00.000000",
  "bot_active": true
}
```

### 6. Monitorar Logs

No painel do Railway:
1. Clique no seu projeto
2. Vá em "Deployments"
3. Clique no deployment ativo
4. Veja os logs em tempo real

Você verá:
```
INFO:     Started server process
INFO:     Waiting for application startup.
Bot started - trading cycle every 60s
INFO:     Application startup complete.
```

### 7. Testar Endpoints

**Health Check:**
```bash
curl https://seu-app.railway.app/
```

**Status Detalhado:**
```bash
curl https://seu-app.railway.app/status
```

### 8. Parar o Bot (Emergência)

**Sem redeploy:**
No Railway, adicione a variável:
```
EMERGENCY_STOP=true
```

O bot irá parar na próxima verificação (máx 60s).

**Com redeploy:**
Pause o serviço no painel do Railway.

## Troubleshooting

### Bot não inicia

**Erro: "Invalid API credentials"**
- Verifique se as variáveis `API_KEY_BINANCE_TESTNET` e `API_SECRET_BINANCE_TESTNET` estão corretas
- Certifique-se de que está usando as chaves do Testnet se `MODE=TESTNET`

**Erro: "Failed to connect to Binance API"**
- Verifique sua conexão de internet
- Teste as credenciais manualmente

### Bot consome muita CPU

- Aumente `REFRESH_INTERVAL` para 120 ou 180 segundos
- Verifique se não há loops infinitos nos logs

### Bot não executa trades

- Verifique `ENABLE_TRADING=true`
- Verifique `EMERGENCY_STOP=false`
- Verifique se há saldo suficiente (`MIN_POSITION_SIZE_USDT=10.0`)
- Verifique logs para ver se sinais estão sendo rejeitados

### Telegram não envia notificações

- Verifique `TELEGRAM_ENABLED=true`
- Verifique se o `TELEGRAM_TOKEN` está correto
- Verifique se o `TELEGRAM_CHAT_ID` está correto
- Inicie uma conversa com o bot do Telegram primeiro

## Custos Railway (Plano Gratuito)

- **Horas gratuitas:** 500 horas/mês
- **RAM:** 512MB (suficiente para o bot)
- **CPU:** Compartilhada
- **Limite de execução:** ~21 dias contínuos

**Dica:** O bot foi otimizado para consumir o mínimo de recursos e rodar dentro do plano gratuito.

## Migrar para Produção (SPOT)

⚠️ **ATENÇÃO: Use apenas quando estiver 100% confiante!**

1. Obtenha API keys da Binance Real (Spot)
2. No Railway, altere as variáveis:
```env
MODE=SPOT
API_KEY_BINANCE_REAL=sua_chave_real
API_SECRET_BINANCE_REAL=seu_secret_real
```
3. Monitore de perto nas primeiras horas
4. Configure alertas no Telegram

## Backup e Segurança

- ✅ Nunca compartilhe suas API keys
- ✅ Use API keys com permissões mínimas (apenas trading, sem withdraw)
- ✅ Configure IP whitelist na Binance (se possível)
- ✅ Monitore regularmente via Telegram
- ✅ Mantenha `EMERGENCY_STOP` sempre acessível

## Suporte

Para problemas técnicos:
1. Verifique os logs no Railway
2. Verifique as notificações do Telegram
3. Teste localmente primeiro: `python main.py`
