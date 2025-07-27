"""
WebSocket client for real-time market data from Binance
"""

import websocket
import json
import threading
import time
from .logger import setup_logger

logger = setup_logger()

class WebSocketClient:
    def __init__(self, testnet=True):
        """
        Initialize WebSocket client for Binance Futures
        
        Args:
            testnet (bool): Use testnet if True
        """
        if testnet:
            self.base_url = "wss://stream.binancefuture.com/ws/btcusdt@ticker"
        else:
            self.base_url = "wss://fstream.binance.com/ws/btcusdt@ticker"
        
        self.ws = None
        self.is_running = False
        self.subscriptions = {}
        self.callbacks = {}
        
        logger.info(f"WebSocket client initialized - Testnet: {testnet}")
    
    def connect(self):
        """Establish WebSocket connection"""
        try:
            self.ws = websocket.WebSocketApp(
                self.base_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start WebSocket in a separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Wait for connection to establish
            timeout = 10
            start_time = time.time()
            while not self.is_running and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.is_running:
                logger.info("WebSocket connection established")
                return True
            else:
                logger.error("WebSocket connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {str(e)}")
            return False
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            self.is_running = False
            self.ws.close()
            logger.info("WebSocket connection closed")
    
    def is_connected(self):
        """Check if WebSocket is connected"""
        return self.is_running
    
    def subscribe_ticker(self, symbol, callback=None):
        """
        Subscribe to 24hr ticker statistics
        
        Args:
            symbol (str): Trading symbol (e.g., 'btcusdt')
            callback (function): Callback function for data
        """
        stream = f"{symbol.lower()}@ticker"
        self._subscribe(stream, callback)
    
    def subscribe_kline(self, symbol, interval, callback=None):
        """
        Subscribe to kline/candlestick data
        
        Args:
            symbol (str): Trading symbol
            interval (str): Kline interval (1m, 5m, 15m, 1h, etc.)
            callback (function): Callback function for data
        """
        stream = f"{symbol.lower()}@kline_{interval}"
        self._subscribe(stream, callback)
    
    def subscribe_depth(self, symbol, levels=5, callback=None):
        """
        Subscribe to order book depth
        
        Args:
            symbol (str): Trading symbol
            levels (int): Number of levels (5, 10, 20)
            callback (function): Callback function for data
        """
        stream = f"{symbol.lower()}@depth{levels}"
        self._subscribe(stream, callback)
    
    def subscribe_trades(self, symbol, callback=None):
        """
        Subscribe to trade streams
        
        Args:
            symbol (str): Trading symbol
            callback (function): Callback function for data
        """
        stream = f"{symbol.lower()}@aggTrade"
        self._subscribe(stream, callback)
    
    def subscribe_mini_ticker_all(self, callback=None):
        """
        Subscribe to all symbols mini ticker
        
        Args:
            callback (function): Callback function for data
        """
        stream = "!miniTicker@arr"
        self._subscribe(stream, callback)
    
    def _subscribe(self, stream, callback=None):
        """
        Internal method to subscribe to a stream
        
        Args:
            stream (str): Stream name
            callback (function): Callback function for data
        """
        if not self.is_running:
            logger.error("WebSocket not connected")
            return False
        
        # Store subscription and callback
        self.subscriptions[stream] = True
        if callback:
            self.callbacks[stream] = callback
        
        # Send subscription message
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [stream],
            "id": int(time.time())
        }
        
        try:
            self.ws.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to stream: {stream}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to {stream}: {str(e)}")
            return False
    
    def unsubscribe(self, stream):
        """
        Unsubscribe from a stream
        
        Args:
            stream (str): Stream name
        """
        if not self.is_running:
            logger.error("WebSocket not connected")
            return False
        
        unsubscribe_msg = {
            "method": "UNSUBSCRIBE",
            "params": [stream],
            "id": int(time.time())
        }
        
        try:
            self.ws.send(json.dumps(unsubscribe_msg))
            
            # Remove from subscriptions and callbacks
            if stream in self.subscriptions:
                del self.subscriptions[stream]
            if stream in self.callbacks:
                del self.callbacks[stream]
            
            logger.info(f"Unsubscribed from stream: {stream}")
            return True
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {stream}: {str(e)}")
            return False
    
    def _on_open(self, ws):
        """WebSocket on_open callback"""
        self.is_running = True
        logger.info("WebSocket connection opened")
    
    def _on_message(self, ws, message):
        """
        WebSocket on_message callback
        
        Args:
            ws: WebSocket instance
            message (str): Received message
        """
        try:
            data = json.loads(message)
            
            # Handle subscription confirmations
            if 'result' in data:
                logger.debug(f"Subscription result: {data}")
                return
            
            # Handle stream data
            if 'stream' in data:
                stream = data['stream']
                stream_data = data['data']
                
                # Call registered callback if exists
                if stream in self.callbacks:
                    try:
                        self.callbacks[stream](stream_data)
                    except Exception as e:
                        logger.error(f"Callback error for {stream}: {str(e)}")
                
                logger.debug(f"Received data for stream: {stream}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
    
    def _on_error(self, ws, error):
        """
        WebSocket on_error callback
        
        Args:
            ws: WebSocket instance
            error: Error object
        """
        logger.error(f"WebSocket error: {str(error)}")
    
    def _on_close(self, ws, close_status_code=None, close_msg=None):
        """
        WebSocket on_close callback
        
        Args:
            ws: WebSocket instance
            close_status_code: Close status code
            close_msg: Close message
        """
        self.is_running = False
        logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
    
    def get_subscriptions(self):
        """Get current subscriptions"""
        return list(self.subscriptions.keys())
    
    def ping(self):
        """Send ping to keep connection alive"""
        if self.is_running and self.ws:
            try:
                self.ws.ping()
                return True
            except Exception as e:
                logger.error(f"Failed to ping WebSocket: {str(e)}")
                return False
        return False
