"""
Trading Bot Background Worker
Executes trading logic periodically without blocking
"""

import time
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.core.config import get_settings, reload_settings
from src.core.constants import OrderSide, PositionStatus, TradeReason
from src.core.models import Position, Trade, AccountBalance
from src.engines.indicators import IndicatorEngine
from src.engines.strategy import StrategyEngine
from src.engines.execution import ExecutionEngine
from src.modules.risk_manager import RiskManager
from src.modules.daily_controller import DailyController
from src.modules.logger import bot_logger
from src.modules.telegram_notifier import telegram_notifier


class TradingBotBackground:
    """
    Trading bot with APScheduler for periodic execution
    Designed for Railway deployment with minimal CPU usage
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize engines
        self.indicator_engine = IndicatorEngine()
        self.strategy_engine = StrategyEngine()
        self.execution_engine = ExecutionEngine()
        
        # Initialize modules
        self.risk_manager = RiskManager()
        self.daily_controller = DailyController()
        
        # State
        self.is_running = False
        self.current_position: Optional[Position] = None
        self.last_check_time: Optional[datetime] = None
        self.start_time: Optional[datetime] = None
        
        # Scheduler
        self.scheduler = BackgroundScheduler(
            timezone='UTC',
            job_defaults={
                'coalesce': True,  # Combine missed runs
                'max_instances': 1,  # Only one instance at a time
                'misfire_grace_time': 30  # Allow 30s delay
            }
        )
    
    def start(self):
        """Start the trading bot with scheduled execution"""
        self.start_time = datetime.utcnow()
        
        bot_logger.log_startup(
            self.settings.mode.value,
            self.settings.get_config_summary()
        )
        
        # Validate configuration
        if not self._validate_startup():
            bot_logger.error("Startup validation failed")
            return
        
        # Send startup notification
        telegram_notifier.notify_startup(self.settings.get_config_summary())
        
        # Initialize daily stats
        balance = self.execution_engine.get_usdt_balance()
        if balance:
            self.daily_controller.get_or_create_daily_stats(balance.free)
            telegram_notifier.notify_new_day(balance.free)
        
        # Schedule trading cycle (every 60 seconds by default)
        interval = max(self.settings.refresh_interval, 60)  # Minimum 60s
        self.scheduler.add_job(
            self._trading_cycle,
            trigger=IntervalTrigger(seconds=interval),
            id='trading_cycle',
            name='Trading Cycle',
            replace_existing=True
        )
        
        # Schedule daily report (23:59 UTC)
        self.scheduler.add_job(
            self._send_daily_report,
            trigger='cron',
            hour=23,
            minute=59,
            id='daily_report',
            name='Daily Report'
        )
        
        # Schedule new day check (every hour)
        self.scheduler.add_job(
            self._check_new_day,
            trigger=IntervalTrigger(hours=1),
            id='check_new_day',
            name='Check New Day'
        )
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        bot_logger.info(f"Bot started - trading cycle every {interval}s")
        
        # Keep thread alive
        try:
            while self.is_running:
                time.sleep(10)
        except (KeyboardInterrupt, SystemExit):
            self.stop("Interrupted")
    
    def stop(self, reason: str = "Manual stop"):
        """Stop the trading bot"""
        self.is_running = False
        
        # Close any open position
        if self.current_position and self.current_position.status == PositionStatus.OPEN:
            self._close_position(TradeReason.MANUAL_CLOSE)
        
        # Shutdown scheduler
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        
        bot_logger.log_shutdown(reason)
        telegram_notifier.notify_shutdown(reason)
    
    def _validate_startup(self) -> bool:
        """Validate all startup requirements"""
        # Check credentials
        if not self.settings.validate_credentials():
            bot_logger.error("Invalid API credentials")
            return False
        
        # Test API connectivity
        if not self.execution_engine.test_connectivity():
            bot_logger.error("Failed to connect to Binance API")
            return False
        
        # Check account balance
        balance = self.execution_engine.get_usdt_balance()
        if balance is None or balance.free < self.settings.min_position_size_usdt:
            bot_logger.error(f"Insufficient balance: {balance}")
            return False
        
        bot_logger.info(f"Account balance: {balance.free:.2f} USDT")
        
        # Check emergency stop
        if self.settings.emergency_stop:
            bot_logger.error("Emergency stop is active")
            return False
        
        return True
    
    def _trading_cycle(self):
        """Execute one trading cycle - called by scheduler"""
        try:
            self.last_check_time = datetime.utcnow()
            
            # Reload settings to check for emergency stop
            self.settings = reload_settings()
            
            if self.settings.emergency_stop:
                bot_logger.warning("Emergency stop activated")
                telegram_notifier.notify_emergency_stop("Emergency stop flag set")
                self.stop("Emergency stop")
                return
            
            # Check if trading is allowed
            is_allowed, reason = self.daily_controller.is_trading_allowed()
            
            if not is_allowed:
                bot_logger.debug(f"Trading not allowed: {reason}")
                return
            
            # Get current price
            current_price = self.execution_engine.get_current_price()
            if current_price is None:
                bot_logger.warning("Failed to get current price")
                return
            
            # Get account balance
            balance = self.execution_engine.get_usdt_balance()
            if balance is None:
                bot_logger.warning("Failed to get account balance")
                return
            
            # Update daily stats
            daily_stats = self.daily_controller.get_or_create_daily_stats(balance.free)
            
            # If we have an open position, manage it
            if self.current_position and self.current_position.status == PositionStatus.OPEN:
                self._manage_position(current_price, daily_stats)
                return
            
            # Look for new trade opportunity
            self._look_for_entry(current_price, balance, daily_stats)
            
        except Exception as e:
            bot_logger.exception(f"Error in trading cycle: {e}")
            telegram_notifier.notify_error("Trading Cycle Error", str(e))
    
    def _look_for_entry(self, current_price: float, balance: AccountBalance, daily_stats):
        """Look for trade entry opportunity"""
        # Get historical data
        df = self.execution_engine.get_klines(limit=500)
        if df is None or df.empty:
            bot_logger.warning("Failed to get historical data")
            return
        
        # Analyze market
        signal = self.strategy_engine.analyze(df, current_price)
        
        # Log signal analysis (reduced verbosity)
        if signal.is_valid:
            bot_logger.log_signal_analysis({
                "current_price": current_price,
                "signal_type": signal.signal_type.value,
                "confluence_score": signal.confluence.percentage,
                "is_valid": signal.is_valid,
            })
        
        # If signal is not valid, return silently
        if not signal.is_valid:
            return
        
        # Assess risk
        risk_assessment = self.risk_manager.assess_trade(
            signal, balance, daily_stats, self.current_position
        )
        
        if not risk_assessment.is_allowed:
            bot_logger.log_signal_rejected(
                risk_assessment.reject_reason.value if risk_assessment.reject_reason else "Unknown",
                {"message": risk_assessment.reject_message}
            )
            return
        
        # Execute entry
        self._execute_entry(signal, risk_assessment)
    
    def _execute_entry(self, signal, risk_assessment):
        """Execute trade entry"""
        # Send notification about signal
        telegram_notifier.notify_signal_analysis(signal)
        
        # Place market order
        success, order = self.execution_engine.place_market_order(
            OrderSide.BUY,
            risk_assessment.position_size_btc
        )
        
        if not success or order is None:
            bot_logger.error("Failed to place entry order")
            telegram_notifier.notify_error("Order Error", "Failed to place entry order")
            return
        
        # Create position
        self.current_position = Position(
            symbol=self.settings.symbol,
            status=PositionStatus.OPEN,
            side=OrderSide.BUY,
            entry_price=order.executed_price,
            quantity=order.executed_qty,
            current_price=order.executed_price,
            stop_loss=risk_assessment.stop_loss_price,
            take_profit=risk_assessment.take_profit_price,
            entry_order_id=order.order_id,
            opened_at=datetime.utcnow(),
        )
        
        bot_logger.log_trade_entry({
            "side": "BUY",
            "entry_price": order.executed_price,
            "quantity": order.executed_qty,
            "stop_loss": risk_assessment.stop_loss_price,
            "take_profit": risk_assessment.take_profit_price,
        })
        
        telegram_notifier.notify_trade_entry(self.current_position, signal)
    
    def _manage_position(self, current_price: float, daily_stats):
        """Manage open position"""
        if self.current_position is None:
            return
        
        # Update position P&L
        self.current_position.update_pnl(current_price)
        
        # Check if should close
        should_close, reason = self.risk_manager.should_close_position(
            self.current_position, current_price, daily_stats
        )
        
        if should_close:
            self._close_position(TradeReason(reason) if reason in [e.value for e in TradeReason] else TradeReason.MANUAL_CLOSE)
    
    def _close_position(self, reason: TradeReason):
        """Close the current position"""
        if self.current_position is None or self.current_position.status != PositionStatus.OPEN:
            return
        
        # Place sell order
        success, order = self.execution_engine.place_market_order(
            OrderSide.SELL,
            self.current_position.quantity
        )
        
        if not success or order is None:
            bot_logger.error("Failed to place exit order")
            telegram_notifier.notify_error("Order Error", "Failed to place exit order")
            return
        
        # Create trade record
        trade = Trade(
            trade_id=f"TRADE_{int(datetime.utcnow().timestamp())}",
            symbol=self.settings.symbol,
            side=OrderSide.BUY,
            entry_price=self.current_position.entry_price,
            exit_price=order.executed_price,
            quantity=order.executed_qty,
            exit_reason=reason,
            entry_time=self.current_position.opened_at or datetime.utcnow(),
            exit_time=datetime.utcnow(),
        )
        
        # Calculate P&L
        entry_fee = self.current_position.entry_price * self.current_position.quantity * 0.001
        exit_fee = order.commission
        trade.commission = entry_fee + exit_fee
        trade.calculate_pnl()
        
        bot_logger.log_trade_exit({
            "exit_price": order.executed_price,
            "net_pnl": trade.net_pnl,
            "pnl_percent": trade.pnl_percent,
            "exit_reason": reason.value,
        })
        
        telegram_notifier.notify_trade_exit(trade)
        
        # Update daily stats
        balance = self.execution_engine.get_usdt_balance()
        if balance:
            daily_stats = self.daily_controller.update_after_trade(trade, balance.free)
            
            # Check if daily target reached
            if daily_stats.target_reached:
                bot_logger.log_daily_target_reached(daily_stats.to_dict())
                telegram_notifier.notify_daily_target_reached(daily_stats)
            
            # Check if max loss reached
            if daily_stats.daily_pnl_percent <= -self.settings.max_daily_loss:
                telegram_notifier.notify_max_loss_reached(daily_stats)
        
        # Clear position
        self.current_position.status = PositionStatus.CLOSED
        self.current_position.closed_at = datetime.utcnow()
        self.current_position = None
    
    def _check_new_day(self):
        """Check if it's a new day and reset if needed"""
        balance = self.execution_engine.get_usdt_balance()
        if balance:
            stats = self.daily_controller.get_or_create_daily_stats(balance.free)
            
            # If stats were just created (new day), send notification
            if stats.total_trades == 0 and not stats.target_reached:
                telegram_notifier.notify_new_day(balance.free)
    
    def _send_daily_report(self):
        """Send daily report"""
        report = self.daily_controller.get_daily_report()
        bot_logger.log_daily_report(report)
        telegram_notifier.notify_daily_report(report)
