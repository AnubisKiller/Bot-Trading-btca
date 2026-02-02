# Conservative BTC Trading Bot - Railway Edition

Bot de trading automatizado otimizado para rodar 24/7 no Railway com consumo mínimo de recursos.

## Características

- ✅ FastAPI com endpoint HTTP para health check
- ✅ Execução periódica em background (APScheduler)
- ✅ Sem loop infinito bloqueante
- ✅ Consumo otimizado de CPU/RAM
- ✅ Todas as configurações via variáveis de ambiente
- ✅ Compatível com Railway (plano gratuito)

## Estrutura

```
bot_railway/
├── main.py              # FastAPI server + inicialização
├── trader.py            # Lógica de trading em background
├── src/                 # Módulos originais do bot
│   ├── core/           # Configuração e modelos
│   ├── engines/        # Indicadores, estratégia, execução
│   └── modules/        # Risk manager, logger, telegram
├── requirements.txt     # Dependências
└── .env.example        # Exemplo de configuração
```

## Deploy no Railway

### 1. Criar projeto no Railway

1. Acesse [railway.app](https://railway.app)
2. Crie um novo projeto
3. Conecte seu repositório GitHub ou faça deploy direto

### 2. Configurar variáveis de ambiente

No painel do Railway, adicione as seguintes variáveis:

**Obrigatórias:**
```
MODE=TESTNET
API_KEY_BINANCE_TESTNET=sua_chave_api
API_SECRET_BINANCE_TESTNET=seu_secret_api
TELEGRAM_TOKEN=seu_token_telegram
TELEGRAM_CHAT_ID=seu_chat_id
```

**Opcionais (já têm valores padrão):**
```
SYMBOL=BTCUSDT
DAILY_TARGET=0.0003
MAX_RISK_PER_TRADE=0.01
REFRESH_INTERVAL=60
LOG_LEVEL=INFO
```

### 3. Configurar comando de start

No Railway, configure o comando de start:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 4. Deploy

O Railway irá automaticamente:
- Instalar dependências do `requirements.txt`
- Executar o comando de start
- Expor a porta HTTP

## Endpoints

- `GET /` - Health check (retorna status do bot)
- `GET /status` - Status detalhado (posição, uptime, etc)

## Funcionamento

1. O FastAPI inicia e mantém uma porta HTTP aberta
2. No startup, o bot é iniciado em uma thread background
3. O APScheduler executa o ciclo de trading a cada 60s (configurável)
4. Não há loop infinito bloqueante
5. O bot verifica mercado, gerencia posições e executa trades periodicamente

## Logs

Os logs são enviados para:
- Console (visível no Railway)
- Telegram (se configurado)

## Monitoramento

Acesse `https://seu-app.railway.app/` para verificar se o bot está rodando.

Resposta esperada:
```json
{
  "status": "running",
  "timestamp": "2026-02-02T12:00:00",
  "bot_active": true
}
```

## Segurança

⚠️ **IMPORTANTE:**
- Nunca commite o arquivo `.env` com suas chaves
- Use sempre variáveis de ambiente no Railway
- Teste primeiro no TESTNET antes de usar modo SPOT
- Configure `EMERGENCY_STOP=true` para parar o bot sem fazer redeploy

## Otimizações para Railway

- Intervalo mínimo de 60s entre verificações
- Logs reduzidos (sem prints excessivos)
- APScheduler com `coalesce=True` (evita acúmulo de jobs)
- FastAPI com `access_log=False` (reduz ruído)
- Thread daemon para não bloquear shutdown

## Suporte

Para dúvidas sobre a estratégia de trading, consulte a documentação original em `docs/STRATEGY.md`.
