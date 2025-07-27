"""
OCO (One-Cancels-Other) order handler
Allows placing two orders simultaneously where execution of one cancels the other
"""

import time
from ..logger import setup_logger, log_trade, log_error

logger = setup_logger()

class OCOOrderHandler:
    def __init__(self, binance_client):
        """
        Initialize OCO order handler
        
        Args:
            binance_client: Binance API client instance
        """
        self.client = binance_client
        logger.info("OCO order handler initialized")
    
    def place_order(self, symbol, side, quantity, price, stop_price, stop_limit_price, 
                   time_in_force='GTC', stop_limit_time_in_force='GTC'):
        """
        Place OCO order
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side ('BUY' or 'SELL')
            quantity (float): Order quantity
            price (float): Limit order price
            stop_price (float): Stop price for stop-limit order
            stop_limit_price (float): Limit price for stop-limit order
            time_in_force (str): Time in force for limit order
            stop_limit_time_in_force (str): Time in force for stop-limit order
        
        Returns:
            dict: OCO order response or None if failed
        """
        try:
            # Prepare OCO order parameters
            order_params = {
                'quantity': quantity,
                'price': price,
                'stopPrice': stop_price,
                'stopLimitPrice': stop_limit_price,
                'timeInForce': time_in_force,
                'stopLimitTimeInForce': stop_limit_time_in_force
            }
            
            # Log the order attempt
            log_trade(
                logger,
                'OCO',
                symbol,
                side,
                quantity,
                price=price,
                status='ATTEMPTING'
            )
            
            # Place OCO order using direct API call
            response = self._place_oco_order(symbol, side, **order_params)
            
            if response:
                # Log successful order
                order_list_id = response.get('orderListId', 'Unknown')
                
                log_trade(
                    logger,
                    'OCO',
                    symbol,
                    side,
                    quantity,
                    price=price,
                    order_id=order_list_id,
                    status='NEW'
                )
                
                logger.info(f"OCO order placed successfully: {order_list_id}")
                return response
            else:
                # Log failed order
                log_error(
                    logger,
                    'OCO_ORDER_PLACEMENT',
                    f"Failed to place OCO order: {symbol} {side} {quantity}"
                )
                return None
                
        except Exception as e:
            error_msg = f"Error placing OCO order: {str(e)}"
            log_error(
                logger,
                'OCO_ORDER_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'stop_price': stop_price,
                    'stop_limit_price': stop_limit_price
                }
            )
            return None
    
    def _place_oco_order(self, symbol, side, **kwargs):
        """
        Internal method to simulate OCO order using separate orders
        Note: Binance Futures API doesn't support native OCO, so we use limit + stop orders
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side
            **kwargs: Order parameters
        
        Returns:
            dict: Simulated OCO response
        """
        try:
            # Extract parameters
            quantity = kwargs.get('quantity')
            price = kwargs.get('price')
            stop_price = kwargs.get('stopPrice')
            time_in_force = kwargs.get('timeInForce', 'GTC')
            
            # Place limit order first (main order)
            limit_params = {
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT',
                'quantity': str(quantity),
                'price': str(price),
                'timeInForce': time_in_force
            }
            
            limit_response = self.client._make_request('POST', '/fapi/v1/order', limit_params, signed=True)
            
            if limit_response:
                logger.info(f"OCO-style limit order placed: {symbol} {side} {quantity} @ {price}")
                
                # Place protective stop order (opposite direction for protection)
                stop_side = 'SELL' if side == 'BUY' else 'BUY'
                stop_params = {
                    'symbol': symbol,
                    'side': stop_side,
                    'type': 'STOP_MARKET',
                    'quantity': str(quantity),
                    'stopPrice': str(stop_price),
                    'timeInForce': 'GTC'
                }
                
                stop_response = self.client._make_request('POST', '/fapi/v1/order', stop_params, signed=True)
                
                return {
                    'orderListId': f"OCO_SIM_{int(time.time())}",
                    'limit_order': limit_response,
                    'stop_order': stop_response,
                    'type': 'OCO_SIMULATION',
                    'status': 'FILLED' if limit_response.get('status') == 'FILLED' else 'NEW'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in OCO simulation: {str(e)}")
            return None
    
    def place_sell_oco(self, symbol, quantity, limit_price, stop_price, stop_limit_price):
        """
        Place sell OCO order (take profit + stop loss)
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Quantity to sell
            limit_price (float): Take profit price (limit order)
            stop_price (float): Stop loss trigger price
            stop_limit_price (float): Stop loss limit price
        
        Returns:
            dict: OCO order response
        """
        return self.place_order(
            symbol, 'SELL', quantity, limit_price, stop_price, stop_limit_price
        )
    
    def place_buy_oco(self, symbol, quantity, limit_price, stop_price, stop_limit_price):
        """
        Place buy OCO order (limit buy + stop buy)
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Quantity to buy
            limit_price (float): Limit buy price
            stop_price (float): Stop buy trigger price
            stop_limit_price (float): Stop buy limit price
        
        Returns:
            dict: OCO order response
        """
        return self.place_order(
            symbol, 'BUY', quantity, limit_price, stop_price, stop_limit_price
        )
    
    def cancel_oco_order(self, symbol, order_list_id):
        """
        Cancel OCO order
        
        Args:
            symbol (str): Trading symbol
            order_list_id (int): OCO order list ID
        
        Returns:
            dict: Cancel response or None if failed
        """
        try:
            params = {
                'symbol': symbol,
                'orderListId': order_list_id,
                'timestamp': int(time.time() * 1000)
            }
            params['signature'] = self.client._generate_signature(params)
            
            response = self.client._make_request('DELETE', '/fapi/v1/orderList', params, signed=True)
            
            if response:
                logger.info(f"OCO order cancelled successfully: {order_list_id}")
                log_trade(
                    logger,
                    'OCO',
                    symbol,
                    'CANCEL',
                    0,
                    order_id=order_list_id,
                    status='CANCELLED'
                )
                return response
            else:
                logger.error(f"Failed to cancel OCO order: {order_list_id}")
                return None
                
        except Exception as e:
            error_msg = f"Error cancelling OCO order: {str(e)}"
            log_error(
                logger,
                'CANCEL_OCO_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'order_list_id': order_list_id
                }
            )
            return None
    
    def get_oco_orders(self, symbol=None):
        """
        Get OCO orders
        
        Args:
            symbol (str, optional): Trading symbol
        
        Returns:
            list: List of OCO orders
        """
        try:
            params = {'timestamp': int(time.time() * 1000)}
            if symbol:
                params['symbol'] = symbol
            
            params['signature'] = self.client._generate_signature(params)
            
            response = self.client._make_request('GET', '/fapi/v1/allOrderList', params, signed=True)
            
            if response is not None:
                logger.info(f"Retrieved {len(response) if response else 0} OCO orders")
                return response
            else:
                logger.error("Failed to retrieve OCO orders")
                return []
                
        except Exception as e:
            logger.error(f"Error getting OCO orders: {str(e)}")
            return []
    
    def create_take_profit_stop_loss(self, symbol, quantity, current_price, 
                                   take_profit_percentage=2.0, stop_loss_percentage=1.0):
        """
        Create OCO order with take profit and stop loss based on percentages
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Position quantity (positive for long, negative for short)
            current_price (float): Current market price
            take_profit_percentage (float): Take profit percentage
            stop_loss_percentage (float): Stop loss percentage
        
        Returns:
            dict: OCO order response
        """
        try:
            # Determine if this is a long or short position
            is_long = quantity > 0
            abs_quantity = abs(quantity)
            
            if is_long:
                # Long position: sell OCO
                take_profit_price = current_price * (1 + take_profit_percentage / 100)
                stop_price = current_price * (1 - stop_loss_percentage / 100)
                stop_limit_price = stop_price * 0.995  # Slightly below stop price
                
                return self.place_sell_oco(
                    symbol, abs_quantity, take_profit_price, stop_price, stop_limit_price
                )
            else:
                # Short position: buy OCO
                take_profit_price = current_price * (1 - take_profit_percentage / 100)
                stop_price = current_price * (1 + stop_loss_percentage / 100)
                stop_limit_price = stop_price * 1.005  # Slightly above stop price
                
                return self.place_buy_oco(
                    symbol, abs_quantity, take_profit_price, stop_price, stop_limit_price
                )
                
        except Exception as e:
            error_msg = f"Error creating TP/SL OCO order: {str(e)}"
            log_error(
                logger,
                'TP_SL_OCO_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'quantity': quantity,
                    'current_price': current_price,
                    'take_profit_percentage': take_profit_percentage,
                    'stop_loss_percentage': stop_loss_percentage
                }
            )
            return None
    
    def monitor_oco_order(self, symbol, order_list_id):
        """
        Monitor OCO order status
        
        Args:
            symbol (str): Trading symbol
            order_list_id (int): OCO order list ID
        
        Returns:
            dict: Order status information
        """
        try:
            params = {
                'symbol': symbol,
                'orderListId': order_list_id,
                'timestamp': int(time.time() * 1000)
            }
            params['signature'] = self.client._generate_signature(params)
            
            response = self.client._make_request('GET', '/fapi/v1/orderList', params, signed=True)
            
            if response:
                status = response.get('listOrderStatus', 'UNKNOWN')
                logger.info(f"OCO order {order_list_id} status: {status}")
                return response
            else:
                logger.error(f"Failed to get OCO order status: {order_list_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error monitoring OCO order: {str(e)}")
            return None
    
    def calculate_risk_reward_ratio(self, entry_price, take_profit_price, stop_loss_price):
        """
        Calculate risk-reward ratio for OCO order
        
        Args:
            entry_price (float): Entry price
            take_profit_price (float): Take profit price
            stop_loss_price (float): Stop loss price
        
        Returns:
            dict: Risk-reward analysis
        """
        try:
            # Determine trade direction
            if take_profit_price > entry_price:
                # Long trade
                reward = take_profit_price - entry_price
                risk = entry_price - stop_loss_price
            else:
                # Short trade
                reward = entry_price - take_profit_price
                risk = stop_loss_price - entry_price
            
            # Calculate ratios
            risk_reward_ratio = reward / risk if risk > 0 else 0
            risk_percentage = (risk / entry_price) * 100
            reward_percentage = (reward / entry_price) * 100
            
            analysis = {
                'risk_amount': risk,
                'reward_amount': reward,
                'risk_reward_ratio': risk_reward_ratio,
                'risk_percentage': risk_percentage,
                'reward_percentage': reward_percentage,
                'is_favorable': risk_reward_ratio >= 2.0  # 1:2 risk-reward minimum
            }
            
            logger.info(f"Risk-reward ratio: 1:{risk_reward_ratio:.2f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error calculating risk-reward ratio: {str(e)}")
            return {}
