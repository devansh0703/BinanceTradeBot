"""
Market order handler for immediate execution at current market price
"""

from .logger import setup_logger, log_trade, log_error

logger = setup_logger()

class MarketOrderHandler:
    def __init__(self, binance_client):
        """
        Initialize market order handler
        
        Args:
            binance_client: Binance API client instance
        """
        self.client = binance_client
        logger.info("Market order handler initialized")
    
    def place_order(self, symbol, side, quantity, reduce_only=False):
        """
        Place market order
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            side (str): Order side ('BUY' or 'SELL')
            quantity (float): Order quantity
            reduce_only (bool): Reduce only flag for closing positions
        
        Returns:
            dict: Order response or None if failed
        """
        try:
            # Prepare order parameters
            order_params = {
                'quantity': quantity,
                'reduceOnly': reduce_only
            }
            
            # Log the order attempt
            log_trade(
                logger, 
                'MARKET', 
                symbol, 
                side, 
                quantity, 
                status='ATTEMPTING'
            )
            
            # Place the order
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                **order_params
            )
            
            if response:
                # Log successful order
                order_id = response.get('orderId', 'Unknown')
                status = response.get('status', 'Unknown')
                
                log_trade(
                    logger,
                    'MARKET',
                    symbol,
                    side,
                    quantity,
                    order_id=order_id,
                    status=status
                )
                
                logger.info(f"Market order placed successfully: {order_id}")
                return response
            else:
                # Log failed order
                log_error(
                    logger,
                    'ORDER_PLACEMENT',
                    f"Failed to place market order: {symbol} {side} {quantity}"
                )
                return None
                
        except Exception as e:
            error_msg = f"Error placing market order: {str(e)}"
            log_error(
                logger,
                'MARKET_ORDER_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'reduce_only': reduce_only
                }
            )
            return None
    
    def place_buy_order(self, symbol, quantity, reduce_only=False):
        """
        Place market buy order
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Quantity to buy
            reduce_only (bool): Reduce only flag
        
        Returns:
            dict: Order response or None if failed
        """
        return self.place_order(symbol, 'BUY', quantity, reduce_only)
    
    def place_sell_order(self, symbol, quantity, reduce_only=False):
        """
        Place market sell order
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Quantity to sell
            reduce_only (bool): Reduce only flag
        
        Returns:
            dict: Order response or None if failed
        """
        return self.place_order(symbol, 'SELL', quantity, reduce_only)
    
    def close_position(self, symbol, position_side='BOTH'):
        """
        Close position using market order
        
        Args:
            symbol (str): Trading symbol
            position_side (str): Position side ('LONG', 'SHORT', or 'BOTH')
        
        Returns:
            list: List of order responses
        """
        try:
            # Get position information
            positions = self.client.get_position_info(symbol)
            
            if not positions:
                logger.warning(f"No position information found for {symbol}")
                return []
            
            orders_placed = []
            
            for position in positions:
                if position['symbol'] != symbol:
                    continue
                
                position_amt = float(position['positionAmt'])
                
                if position_amt == 0:
                    continue  # No position to close
                
                current_side = position['positionSide']
                
                # Skip if not matching requested position side
                if position_side != 'BOTH' and current_side != position_side:
                    continue
                
                # Determine order side to close position
                if position_amt > 0:
                    close_side = 'SELL'
                    close_quantity = abs(position_amt)
                else:
                    close_side = 'BUY'
                    close_quantity = abs(position_amt)
                
                # Place closing order
                response = self.place_order(
                    symbol, 
                    close_side, 
                    close_quantity, 
                    reduce_only=True
                )
                
                if response:
                    orders_placed.append(response)
                    logger.info(f"Position closed: {symbol} {current_side} {close_quantity}")
                else:
                    logger.error(f"Failed to close position: {symbol} {current_side}")
            
            return orders_placed
            
        except Exception as e:
            error_msg = f"Error closing position: {str(e)}"
            log_error(
                logger,
                'CLOSE_POSITION_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'position_side': position_side
                }
            )
            return []
    
    def get_market_price(self, symbol):
        """
        Get current market price for symbol
        
        Args:
            symbol (str): Trading symbol
        
        Returns:
            float: Current market price or None if failed
        """
        try:
            ticker = self.client.get_ticker(symbol)
            
            if ticker and 'price' in ticker:
                return float(ticker['price'])
            else:
                logger.error(f"Failed to get market price for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting market price for {symbol}: {str(e)}")
            return None
    
    def calculate_position_value(self, symbol, quantity):
        """
        Calculate position value at current market price
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Position quantity
        
        Returns:
            float: Position value in USDT or None if failed
        """
        try:
            market_price = self.get_market_price(symbol)
            
            if market_price is not None:
                return abs(quantity) * market_price
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error calculating position value: {str(e)}")
            return None
    
    def validate_market_order(self, symbol, quantity, side='BUY'):
        """
        Validate market order parameters before placement
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Order quantity
            side (str): Order side
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Get exchange info to validate parameters
            exchange_info = self.client.get_exchange_info()
            
            if not exchange_info:
                logger.error("Could not retrieve exchange information")
                return False
            
            # Find symbol info
            symbol_info = None
            for s in exchange_info.get('symbols', []):
                if s['symbol'] == symbol:
                    symbol_info = s
                    break
            
            if not symbol_info:
                logger.error(f"Symbol {symbol} not found in exchange info")
                return False
            
            # Check if symbol is active
            if symbol_info['status'] != 'TRADING':
                logger.error(f"Symbol {symbol} is not actively trading")
                return False
            
            # Validate quantity precision
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'LOT_SIZE':
                    min_qty = float(filter_info['minQty'])
                    max_qty = float(filter_info['maxQty'])
                    step_size = float(filter_info['stepSize'])
                    
                    if quantity < min_qty:
                        logger.error(f"Quantity {quantity} below minimum {min_qty}")
                        return False
                    
                    if quantity > max_qty:
                        logger.error(f"Quantity {quantity} above maximum {max_qty}")
                        return False
                    
                    # Check step size
                    if step_size > 0:
                        remainder = (quantity - min_qty) % step_size
                        if remainder > step_size * 0.001:  # Small tolerance
                            logger.error(f"Quantity {quantity} doesn't match step size {step_size}")
                            return False
            
            logger.info(f"Market order validation passed: {side} {quantity} {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating market order: {str(e)}")
            return False
