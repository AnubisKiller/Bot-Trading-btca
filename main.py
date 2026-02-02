#!/usr/bin/env python3
"""
Conservative BTC Trading Bot - Railway Compatible
FastAPI server with background trading execution
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from threading import Thread
import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import get_settings
from src.modules.logger import bot_logger
from trader import TradingBotBackground

# Initialize FastAPI
app = FastAPI(title="Trading Bot", version="1.0")

# Global bot instance
bot_instance = None
bot_thread = None


@app.get("/")
def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "bot_active": bot_instance.is_running if bot_instance else False
    })


@app.get("/status")
def get_status():
    """Get bot status"""
    if not bot_instance:
        return JSONResponse({"error": "Bot not initialized"}, status_code=503)
    
    return JSONResponse({
        "is_running": bot_instance.is_running,
        "has_position": bot_instance.current_position is not None,
        "last_check": bot_instance.last_check_time.isoformat() if bot_instance.last_check_time else None,
        "uptime_seconds": (datetime.utcnow() - bot_instance.start_time).total_seconds() if bot_instance.start_time else 0
    })


@app.on_event("startup")
async def startup_event():
    """Start bot in background thread on server startup"""
    global bot_instance, bot_thread
    
    bot_logger.info("FastAPI server starting - initializing bot")
    
    # Create bot instance
    bot_instance = TradingBotBackground()
    
    # Start bot in background thread
    bot_thread = Thread(target=bot_instance.start, daemon=True)
    bot_thread.start()
    
    bot_logger.info("Bot background thread started")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop bot gracefully on server shutdown"""
    global bot_instance
    
    if bot_instance:
        bot_logger.info("FastAPI server shutting down - stopping bot")
        bot_instance.stop("Server shutdown")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=False  # Reduce log noise
    )
