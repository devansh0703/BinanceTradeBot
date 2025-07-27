"""
Stop-Limit order handler
Triggers a limit order when a stop price is reached
"""

import time
import threading
from ..logger import setup_logger, log_trade, log_error

logger = setup_logger()

class StopLimitOrderHandler:
    def __init__(self, binance_client):
        """
        Initialize Stop-Limit order handler
        
        Args:
            binance_client: Binance API client instance
        """
        self.client = binance_client
        self.monitoring_orders = {}
        self.monitor_thread = None
        self.is_monitoring = False
        logger.info("Stop-Limit order handler initialized")
    
    def place_order(self, symbol, side, quantity, stop_price, limit_price, 
                   time_in_force='GTC', reduce_only=False, working_type='MARK_PRICE'):
        """
        Place stop-limit order
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side ('BUY' or 'SELL')
            quantity (float): Order quantity
            stop_price (float): Stop trigger price
            limit_price (float): Limit order price after trigger
            time_in_force (str): Time in force
            reduce_only (bool): Reduce only flag
            working_type (str): Price type for trigger ('MARK_PRICE', 'CONTRACT_PRICE')
        
        Returns:
            dict: Order response or None if failed
        """
        try:
            # Prepare order parameters
            order_params = {
                'quantity': quantity,
                'stopPrice': stop_price,
                'price': limit_price,
                'timeInForce': time_in_force,
                'reduceOnly': reduce_only,
                'workingType': working_type
            }
            
            # Log the order attempt
            log_trade(
                logger,
                'STOP_LIMIT',
                symbol,
                side,
                quantity,
                price=limit_price,
                status='ATTEMPTING'
            )
            
            # Place the order
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='STOP',
                **order_params
            )
            
            if response:
                # Log successful order
                order_id = response.get('orderId', 'Unknown')
                status = response.get('status', 'Unknown')
                
                log_trade(
                    logger,
                    'STOP_LIMIT',
                    symbol,
                    side,
                    quantity,
                    price=limit_price,
                    order_id=order_id,
                    status=status
                )
                
                logger.info(f"Stop-limit order placed successfully: {order_id}")
                return response
            else:
                # Log failed order
                log_error(
                    logger,
                    'STOP_LIMIT_PLACEMENT',
                    f"Failed to place stop-limit order: {symbol} {side} {quantity}"
                )
                return None
                
        except Exception as e:
            error_msg = f"Error placing stop-limit order: {str(e)}"
            log_error(
                logger,
                'STOP_LIMIT_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'stop_price': stop_price,
                    'limit_price': limit_price
                }
            )
            return None
    
    def place_stop_loss(self, symbol, quantity, stop_price, limit_price=None):
        """
        Place stop-loss order
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Quantity to sell/buy
            stop_price (float): Stop trigger price
            limit_price (float, optional): Limit price (if None, uses stop_price * 0.99)
        
        Returns:
            dict: Order response
        """
        try:
            # Determine order side based on quantity
            if quantity > 0:
                side = 'SELL'  # Close long position
            else:
                side = 'BUY'   # Close short position
                quantity = abs(quantity)
            
            # Set default limit price if not provided
            if limit_price is None:
                if side == 'SELL':
                    limit_price = stop_price * 0.99  # Slightly below stop for sells
                else:
                    limit_price = stop_price * 1.01  # Slightly above stop for buys
            
            return self.place_order(
                symbol, side, quantity, stop_price, limit_price, reduce_only=True
            )
            
        except Exception as e:
            logger.error(f"Error placing stop-loss order: {str(e)}")
            return None
    
    def place_take_profit(self, symbol, quantity, stop_price, limit_price=None):
        """
        Place take-profit order
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Quantity to sell/buy
            stop_price (float): Trigger price for take profit
            limit_price (float, optional): Limit price
        
        Returns:
            dict: Order response
        """
        try:
            # Determine order side based on quantity
            if quantity > 0:
                side = 'SELL'  # Take profit on long position
            else:
                side = 'BUY'   # Take profit on short position
                quantity = abs(quantity)
            
            # Set default limit price if not provided
            if limit_price is None:
                if side == 'SELL':
                    limit_price = stop_price * 1.01  # Slightly above trigger for sells
                else:
                    limit_price = stop_price * 0.99  # Slightly below trigger for buys
            
            return self.place_order(
                symbol, side, quantity, stop_price, limit_price, reduce_only=True
            )
            
        except Exception as e:
            logger.error(f"Error placing take-profit order: {str(e)}")
            return None
    
    def place_trailing_stop(self, symbol, side, quantity, callback_rate, activation_price=None):
        """
        Place trailing stop order
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side
            quantity (float): Order quantity
            callback_rate (float): Callback rate in percentage
            activation_price (float, optional): Activation price
        
        Returns:
            dict: Order response
        """
        try:
            order_params = {
                'quantity': quantity,
                'callbackRate': callback_rate,
                'reduceOnly': True
            }
            
            if activation_price:
                order_params['activationPrice'] = activation_price
            
            # Log the order attempt
            log_trade(
                logger,
                'TRAILING_STOP',
                symbol,
                side,
                quantity,
                status='ATTEMPTING'
            )
            
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='TRAILING_STOP_MARKET',
                **order_params
            )
            
            if response:
                order_id = response.get('orderId', 'Unknown')
                log_trade(
                    logger,
                    'TRAILING_STOP',
                    symbol,
                    side,
                    quantity,
                    order_id=order_id,
                    status='NEW'
                )
                logger.info(f"Trailing stop order placed: {order_id}")
                return response
            else:
                logger.error("Failed to place trailing stop order")
                return None
                
        except Exception as e:
            error_msg = f"Error placing trailing stop: {str(e)}"
            log_error(
                logger,
                'TRAILING_STOP_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'callback_rate': callback_rate
                }
            )
            return None
    
    def modify_stop_order(self, symbol, order_id, new_stop_price=None, new_limit_price=None):
        """
        Modify existing stop order
        
        Args:
            symbol (str): Trading symbol
            order_id (int): Order ID to modify
            new_stop_price (float, optional): New stop price
            new_limit_price (float, optional): New limit price
        
        Returns:
            dict: Modified order response
        """
        try:
            # Get current order details
            current_order = self.client.get_order_status(symbol, order_id=order_id)
            
            if not current_order:
                logger.error(f"Could not retrieve order {order_id} for modification")
                return None
            
            # Cancel existing order
            cancel_response = self.client.cancel_order(symbol, order_id=order_id)
            
            if not cancel_response:
                logger.error(f"Failed to cancel order {order_id} for modification")
                return None
            
            # Prepare new order parameters
            quantity = float(current_order['origQty'])
            side = current_order['side']
            stop_price = new_stop_price if new_stop_price else float(current_order['stopPrice'])
            limit_price = new_limit_price if new_limit_price else float(current_order['price'])
            
            # Place new order with modified parameters
            new_order = self.place_order(symbol, side, quantity, stop_price, limit_price)
            
            if new_order:
                logger.info(f"Stop order modified: {order_id} -> {new_order.get('orderId')}")
                return new_order
            else:
                logger.error(f"Failed to place modified stop order for {order_id}")
                return None
                
        except Exception as e:
            error_msg = f"Error modifying stop order: {str(e)}"
            log_error(
                logger,
                'MODIFY_STOP_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'order_id': order_id,
                    'new_stop_price': new_stop_price,
                    'new_limit_price': new_limit_price
                }
            )
            return None
    
    def cancel_stop_order(self, symbol, order_id):
        """
        Cancel stop order
        
        Args:
            symbol (str): Trading symbol
            order_id (int): Order ID to cancel
        
        Returns:
            dict: Cancel response
        """
        try:
            response = self.client.cancel_order(symbol, order_id=order_id)
            
            if response:
                logger.info(f"Stop order cancelled: {order_id}")
                log_trade(
                    logger,
                    'STOP_LIMIT',
                    symbol,
                    'CANCEL',
                    0,
                    order_id=order_id,
                    status='CANCELLED'
                )
                return response
            else:
                logger.error(f"Failed to cancel stop order: {order_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error cancelling stop order: {str(e)}")
            return None
    
    def get_stop_orders(self, symbol=None):
        """
        Get active stop orders
        
        Args:
            symbol (str, optional): Trading symbol
        
        Returns:
            list: List of stop orders
        """
        try:
            orders = self.client.get_open_orders(symbol)
            
            if orders is not None:
                # Filter stop orders
                stop_orders = [
                    order for order in orders 
                    if order.get('type') in ['STOP', 'STOP_MARKET', 'TRAILING_STOP_MARKET']
                ]
                logger.info(f"Retrieved {len(stop_orders)} stop orders")
                return stop_orders
            else:
                logger.error("Failed to retrieve stop orders")
                return []
                
        except Exception as e:
            logger.error(f"Error getting stop orders: {str(e)}")
            return []
    
    def calculate_stop_levels(self, entry_price, position_side, risk_percentage=2.0, reward_ratio=2.0):
        """
        Calculate stop loss and take profit levels
        
        Args:
            entry_price (float): Entry price
            position_side (str): Position side ('LONG' or 'SHORT')
            risk_percentage (float): Risk percentage
            reward_ratio (float): Risk-reward ratio
        
        Returns:
            dict: Stop loss and take profit levels
        """
        try:
            risk_amount = entry_price * (risk_percentage / 100)
            reward_amount = risk_amount * reward_ratio
            
            if position_side.upper() == 'LONG':
                stop_loss = entry_price - risk_amount
                take_profit = entry_price + reward_amount
            else:  # SHORT
                stop_loss = entry_price + risk_amount
                take_profit = entry_price - reward_amount
            
            levels = {
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_amount': risk_amount,
                'reward_amount': reward_amount,
                'risk_percentage': risk_percentage,
                'reward_percentage': (reward_amount / entry_price) * 100,
                'risk_reward_ratio': reward_ratio
            }
            
            logger.info(f"Stop levels calculated for {position_side}: SL={stop_loss:.4f}, TP={take_profit:.4f}")
            return levels
            
        except Exception as e:
            logger.error(f"Error calculating stop levels: {str(e)}")
            return {}
    
    def create_bracket_stop_orders(self, symbol, entry_order_id, position_side, risk_percentage=2.0):
        """
        Create bracket stop orders after entry order fills
        
        Args:
            symbol (str): Trading symbol
            entry_order_id (int): Entry order ID
            position_side (str): Position side
            risk_percentage (float): Risk percentage
        
        Returns:
            dict: Created stop orders
        """
        try:
            # Get entry order details
            entry_order = self.client.get_order_status(symbol, order_id=entry_order_id)
            
            if not entry_order or entry_order.get('status') != 'FILLED':
                logger.error(f"Entry order {entry_order_id} not filled yet")
                return {}
            
            entry_price = float(entry_order['avgPrice'])
            quantity = float(entry_order['executedQty'])
            
            # Calculate stop levels
            levels = self.calculate_stop_levels(entry_price, position_side, risk_percentage)
            
            if not levels:
                return {}
            
            orders = {}
            
            # Place stop loss
            sl_order = self.place_stop_loss(symbol, quantity, levels['stop_loss'])
            if sl_order:
                orders['stop_loss'] = sl_order
            
            # Place take profit
            tp_order = self.place_take_profit(symbol, quantity, levels['take_profit'])
            if tp_order:
                orders['take_profit'] = tp_order
            
            logger.info(f"Bracket stop orders created for {symbol}")
            return orders
            
        except Exception as e:
            logger.error(f"Error creating bracket stop orders: {str(e)}")
            return {}
    
    def monitor_price_for_manual_stops(self, symbol, stop_conditions):
        """
        Monitor price for manual stop conditions (for exchanges without native stop orders)
        
        Args:
            symbol (str): Trading symbol
            stop_conditions (list): List of stop conditions
        
        Returns:
            str: Monitor ID
        """
        try:
            monitor_id = f"MONITOR_{symbol}_{int(time.time())}"
            
            self.monitoring_orders[monitor_id] = {
                'symbol': symbol,
                'conditions': stop_conditions,
                'active': True
            }
            
            # Start monitoring thread if not already running
            if not self.is_monitoring:
                self.is_monitoring = True
                self.monitor_thread = threading.Thread(
                    target=self._price_monitor_loop,
                    daemon=True
                )
                self.monitor_thread.start()
            
            logger.info(f"Price monitoring started for {symbol}: {monitor_id}")
            return monitor_id
            
        except Exception as e:
            logger.error(f"Error starting price monitoring: {str(e)}")
            return None
    
    def _price_monitor_loop(self):
        """
        Main price monitoring loop
        """
        try:
            while self.is_monitoring and self.monitoring_orders:
                for monitor_id, monitor_data in list(self.monitoring_orders.items()):
                    if not monitor_data['active']:
                        continue
                    
                    symbol = monitor_data['symbol']
                    conditions = monitor_data['conditions']
                    
                    # Get current price
                    ticker = self.client.get_ticker(symbol)
                    if not ticker:
                        continue
                    
                    current_price = float(ticker['price'])
                    
                    # Check conditions
                    for condition in conditions:
                        if self._check_stop_condition(current_price, condition):
                            # Execute stop order
                            self._execute_manual_stop(condition)
                            
                            # Remove executed condition
                            conditions.remove(condition)
                    
                    # Remove monitor if no conditions left
                    if not conditions:
                        del self.monitoring_orders[monitor_id]
                
                time.sleep(1)  # Check every second
                
        except Exception as e:
            logger.error(f"Error in price monitoring loop: {str(e)}")
        finally:
            self.is_monitoring = False
    
    def _check_stop_condition(self, current_price, condition):
        """
        Check if stop condition is met
        
        Args:
            current_price (float): Current market price
            condition (dict): Stop condition
        
        Returns:
            bool: True if condition is met
        """
        try:
            trigger_price = condition['trigger_price']
            trigger_type = condition['trigger_type']  # 'above' or 'below'
            
            if trigger_type == 'above':
                return current_price >= trigger_price
            elif trigger_type == 'below':
                return current_price <= trigger_price
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking stop condition: {str(e)}")
            return False
    
    def _execute_manual_stop(self, condition):
        """
        Execute manual stop order
        
        Args:
            condition (dict): Stop condition with order details
        """
        try:
            symbol = condition['symbol']
            side = condition['side']
            quantity = condition['quantity']
            order_type = condition.get('order_type', 'MARKET')
            
            if order_type == 'MARKET':
                from ..market_orders import MarketOrderHandler
                market_handler = MarketOrderHandler(self.client)
                response = market_handler.place_order(symbol, side, quantity)
            else:
                limit_price = condition.get('limit_price')
                response = self.client.place_order(
                    symbol=symbol,
                    side=side,
                    order_type='LIMIT',
                    quantity=quantity,
                    price=limit_price
                )
            
            if response:
                logger.info(f"Manual stop executed: {response.get('orderId')}")
            else:
                logger.error("Failed to execute manual stop")
                
        except Exception as e:
            logger.error(f"Error executing manual stop: {str(e)}")
