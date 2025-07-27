"""
Logging configuration for the trading bot
"""

import logging
import os
from datetime import datetime

def setup_logger(name="trading_bot", log_file="bot.log", level=logging.INFO):
    """
    Set up logger with file and console handlers
    
    Args:
        name (str): Logger name
        log_file (str): Log file path
        level: Logging level
    
    Returns:
        logging.Logger: Configured logger
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding multiple handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Log the initialization
    logger.info("=" * 50)
    logger.info(f"Trading Bot Logger Initialized - {datetime.now()}")
    logger.info("=" * 50)
    
    return logger

def log_trade(logger, trade_type, symbol, side, quantity, price=None, order_id=None, status="PENDING"):
    """
    Log trading activity in a structured format
    
    Args:
        logger: Logger instance
        trade_type (str): Type of trade (MARKET, LIMIT, etc.)
        symbol (str): Trading symbol
        side (str): BUY or SELL
        quantity (float): Trade quantity
        price (float, optional): Trade price
        order_id (str, optional): Order ID
        status (str): Trade status
    """
    
    trade_info = {
        'type': trade_type,
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'price': price,
        'order_id': order_id,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }
    
    log_message = f"TRADE: {trade_type} {side} {quantity} {symbol}"
    if price:
        log_message += f" @ {price}"
    if order_id:
        log_message += f" (ID: {order_id})"
    log_message += f" - {status}"
    
    logger.info(log_message)
    logger.debug(f"Trade details: {trade_info}")

def log_error(logger, error_type, error_message, additional_data=None):
    """
    Log errors in a structured format
    
    Args:
        logger: Logger instance
        error_type (str): Type of error
        error_message (str): Error message
        additional_data (dict, optional): Additional error data
    """
    
    error_info = {
        'error_type': error_type,
        'message': error_message,
        'timestamp': datetime.now().isoformat(),
        'additional_data': additional_data
    }
    
    logger.error(f"ERROR [{error_type}]: {error_message}")
    if additional_data:
        logger.debug(f"Error details: {error_info}")

def log_market_data(logger, symbol, price, volume=None, indicators=None):
    """
    Log market data updates
    
    Args:
        logger: Logger instance
        symbol (str): Trading symbol
        price (float): Current price
        volume (float, optional): Trading volume
        indicators (dict, optional): Technical indicators
    """
    
    market_info = {
        'symbol': symbol,
        'price': price,
        'volume': volume,
        'indicators': indicators,
        'timestamp': datetime.now().isoformat()
    }
    
    log_message = f"MARKET: {symbol} @ {price}"
    if volume:
        log_message += f" (Vol: {volume})"
    
    logger.debug(log_message)
    if indicators:
        logger.debug(f"Indicators: {indicators}")

def log_websocket_event(logger, event_type, symbol=None, data=None):
    """
    Log WebSocket events
    
    Args:
        logger: Logger instance
        event_type (str): Type of WebSocket event
        symbol (str, optional): Trading symbol
        data (dict, optional): Event data
    """
    
    ws_info = {
        'event_type': event_type,
        'symbol': symbol,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    
    log_message = f"WEBSOCKET [{event_type}]"
    if symbol:
        log_message += f" - {symbol}"
    
    logger.debug(log_message)
    if data:
        logger.debug(f"WebSocket data: {data}")

def log_strategy_signal(logger, strategy_name, signal, confidence, details=None):
    """
    Log trading strategy signals
    
    Args:
        logger: Logger instance
        strategy_name (str): Name of the strategy
        signal (str): Trading signal (BUY, SELL, HOLD)
        confidence (float): Signal confidence (0-1)
        details (dict, optional): Signal details
    """
    
    signal_info = {
        'strategy': strategy_name,
        'signal': signal,
        'confidence': confidence,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    
    log_message = f"SIGNAL [{strategy_name}]: {signal} (confidence: {confidence:.2f})"
    
    logger.info(log_message)
    if details:
        logger.debug(f"Signal details: {signal_info}")
