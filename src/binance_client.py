"""
Binance Futures API client for trading operations
"""

import hashlib
import hmac
import time
import requests
import json
from urllib.parse import urlencode
from .logger import setup_logger

logger = setup_logger()

class BinanceClient:
    def __init__(self, api_key, api_secret, testnet=True):
        """
        Initialize Binance Futures client
        
        Args:
            api_key (str): Binance API key
            api_secret (str): Binance API secret
            testnet (bool): Use testnet if True, live trading if False
        """
        self.api_key = api_key
        self.api_secret = api_secret
        
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
        
        logger.info(f"Binance client initialized - Testnet: {testnet}")
    
    def _generate_signature(self, params):
        """Generate HMAC SHA256 signature for API requests"""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method, endpoint, params=None, signed=False):
        """
        Make API request to Binance
        
        Args:
            method (str): HTTP method (GET, POST, DELETE)
            endpoint (str): API endpoint
            params (dict): Request parameters
            signed (bool): Whether request needs signature
        
        Returns:
            dict: API response
        """
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params)
            elif method == 'POST':
                response = self.session.post(url, params=params)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"API request successful: {method} {endpoint}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {endpoint} - {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"API error response: {error_data}")
                except:
                    logger.error(f"API error response: {e.response.text}")
            return None
    
    def get_server_time(self):
        """Get server time"""
        return self._make_request('GET', '/fapi/v1/time')
    
    def get_exchange_info(self):
        """Get exchange trading rules and symbol information"""
        return self._make_request('GET', '/fapi/v1/exchangeInfo')
    
    def get_ticker(self, symbol):
        """
        Get 24hr ticker price change statistics
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
        
        Returns:
            dict: Ticker data
        """
        params = {'symbol': symbol}
        return self._make_request('GET', '/fapi/v1/ticker/24hr', params)
    
    def get_orderbook(self, symbol, limit=100):
        """
        Get order book for symbol
        
        Args:
            symbol (str): Trading symbol
            limit (int): Number of entries to return
        
        Returns:
            dict: Order book data
        """
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/fapi/v1/depth', params)
    
    def get_klines(self, symbol, interval, limit=500, start_time=None, end_time=None):
        """
        Get kline/candlestick data
        
        Args:
            symbol (str): Trading symbol
            interval (str): Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit (int): Number of klines to return (max 1500)
            start_time (int): Start time in milliseconds
            end_time (int): End time in milliseconds
        
        Returns:
            list: Kline data
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self._make_request('GET', '/fapi/v1/klines', params)
    
    def get_account_info(self):
        """Get account information"""
        return self._make_request('GET', '/fapi/v2/account', signed=True)
    
    def get_position_info(self, symbol=None):
        """
        Get position information
        
        Args:
            symbol (str, optional): Trading symbol
        
        Returns:
            list: Position information
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request('GET', '/fapi/v2/positionRisk', params, signed=True)
    
    def get_open_orders(self, symbol=None):
        """
        Get open orders
        
        Args:
            symbol (str, optional): Trading symbol
        
        Returns:
            list: Open orders
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request('GET', '/fapi/v1/openOrders', params, signed=True)
    
    def place_order(self, symbol, side, order_type, **kwargs):
        """
        Place new order
        
        Args:
            symbol (str): Trading symbol
            side (str): BUY or SELL
            order_type (str): MARKET, LIMIT, STOP, TAKE_PROFIT, etc.
            **kwargs: Additional order parameters
        
        Returns:
            dict: Order response
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type
        }
        
        # Add additional parameters
        for key, value in kwargs.items():
            if value is not None:
                params[key] = value
        
        logger.info(f"Placing order: {params}")
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def cancel_order(self, symbol, order_id=None, orig_client_order_id=None):
        """
        Cancel order
        
        Args:
            symbol (str): Trading symbol
            order_id (int, optional): Order ID
            orig_client_order_id (str, optional): Client order ID
        
        Returns:
            dict: Cancel response
        """
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        logger.info(f"Cancelling order: {params}")
        return self._make_request('DELETE', '/fapi/v1/order', params, signed=True)
    
    def cancel_all_orders(self, symbol):
        """
        Cancel all open orders for symbol
        
        Args:
            symbol (str): Trading symbol
        
        Returns:
            dict: Cancel response
        """
        params = {'symbol': symbol}
        logger.info(f"Cancelling all orders for {symbol}")
        return self._make_request('DELETE', '/fapi/v1/allOpenOrders', params, signed=True)
    
    def get_order_status(self, symbol, order_id=None, orig_client_order_id=None):
        """
        Get order status
        
        Args:
            symbol (str): Trading symbol
            order_id (int, optional): Order ID
            orig_client_order_id (str, optional): Client order ID
        
        Returns:
            dict: Order status
        """
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return self._make_request('GET', '/fapi/v1/order', params, signed=True)
    
    def set_leverage(self, symbol, leverage):
        """
        Change initial leverage
        
        Args:
            symbol (str): Trading symbol
            leverage (int): Leverage value (1-125)
        
        Returns:
            dict: Leverage response
        """
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        
        logger.info(f"Setting leverage for {symbol}: {leverage}x")
        return self._make_request('POST', '/fapi/v1/leverage', params, signed=True)
    
    def change_margin_type(self, symbol, margin_type):
        """
        Change margin type
        
        Args:
            symbol (str): Trading symbol
            margin_type (str): ISOLATED or CROSSED
        
        Returns:
            dict: Margin type response
        """
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        
        logger.info(f"Changing margin type for {symbol}: {margin_type}")
        return self._make_request('POST', '/fapi/v1/marginType', params, signed=True)
