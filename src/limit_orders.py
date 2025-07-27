"""
Limit order handler for orders at specific price levels
"""

from .logger import setup_logger, log_trade, log_error

logger = setup_logger()

class LimitOrderHandler:
    def __init__(self, binance_client):
        """
        Initialize limit order handler
        
        Args:
            binance_client: Binance API client instance
        """
        self.client = binance_client
        logger.info("Limit order handler initialized")
    
    def place_order(self, symbol, side, quantity, price, time_in_force='GTC', reduce_only=False):
        """
        Place limit order
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            side (str): Order side ('BUY' or 'SELL')
            quantity (float): Order quantity
            price (float): Limit price
            time_in_force (str): Time in force ('GTC', 'IOC', 'FOK')
            reduce_only (bool): Reduce only flag for closing positions
        
        Returns:
            dict: Order response or None if failed
        """
        try:
            # Prepare order parameters
            order_params = {
                'quantity': quantity,
                'price': price,
                'timeInForce': time_in_force,
                'reduceOnly': reduce_only
            }
            
            # Log the order attempt
            log_trade(
                logger,
                'LIMIT',
                symbol,
                side,
                quantity,
                price=price,
                status='ATTEMPTING'
            )
            
            # Place the order
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                **order_params
            )
            
            if response:
                # Log successful order
                order_id = response.get('orderId', 'Unknown')
                status = response.get('status', 'Unknown')
                
                log_trade(
                    logger,
                    'LIMIT',
                    symbol,
                    side,
                    quantity,
                    price=price,
                    order_id=order_id,
                    status=status
                )
                
                logger.info(f"Limit order placed successfully: {order_id}")
                return response
            else:
                # Log failed order
                log_error(
                    logger,
                    'ORDER_PLACEMENT',
                    f"Failed to place limit order: {symbol} {side} {quantity} @ {price}"
                )
                return None
                
        except Exception as e:
            error_msg = f"Error placing limit order: {str(e)}"
            log_error(
                logger,
                'LIMIT_ORDER_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'time_in_force': time_in_force,
                    'reduce_only': reduce_only
                }
            )
            return None
    
    def place_buy_limit(self, symbol, quantity, price, time_in_force='GTC', reduce_only=False):
        """
        Place limit buy order
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Quantity to buy
            price (float): Buy price
            time_in_force (str): Time in force
            reduce_only (bool): Reduce only flag
        
        Returns:
            dict: Order response or None if failed
        """
        return self.place_order(symbol, 'BUY', quantity, price, time_in_force, reduce_only)
    
    def place_sell_limit(self, symbol, quantity, price, time_in_force='GTC', reduce_only=False):
        """
        Place limit sell order
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Quantity to sell
            price (float): Sell price
            time_in_force (str): Time in force
            reduce_only (bool): Reduce only flag
        
        Returns:
            dict: Order response or None if failed
        """
        return self.place_order(symbol, 'SELL', quantity, price, time_in_force, reduce_only)
    
    def modify_order(self, symbol, order_id, quantity=None, price=None):
        """
        Modify existing limit order
        
        Args:
            symbol (str): Trading symbol
            order_id (int): Order ID to modify
            quantity (float, optional): New quantity
            price (float, optional): New price
        
        Returns:
            dict: Modified order response or None if failed
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
            
            # Use new values or keep existing ones
            new_quantity = quantity if quantity is not None else float(current_order['origQty'])
            new_price = price if price is not None else float(current_order['price'])
            side = current_order['side']
            
            # Place new order with modified parameters
            new_order = self.place_order(symbol, side, new_quantity, new_price)
            
            if new_order:
                logger.info(f"Order modified successfully: {order_id} -> {new_order.get('orderId')}")
                return new_order
            else:
                logger.error(f"Failed to place modified order for {order_id}")
                return None
                
        except Exception as e:
            error_msg = f"Error modifying order: {str(e)}"
            log_error(
                logger,
                'MODIFY_ORDER_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'order_id': order_id,
                    'quantity': quantity,
                    'price': price
                }
            )
            return None
    
    def cancel_order(self, symbol, order_id):
        """
        Cancel limit order
        
        Args:
            symbol (str): Trading symbol
            order_id (int): Order ID to cancel
        
        Returns:
            dict: Cancel response or None if failed
        """
        try:
            response = self.client.cancel_order(symbol, order_id=order_id)
            
            if response:
                logger.info(f"Order cancelled successfully: {order_id}")
                log_trade(
                    logger,
                    'LIMIT',
                    symbol,
                    'CANCEL',
                    0,
                    order_id=order_id,
                    status='CANCELLED'
                )
                return response
            else:
                logger.error(f"Failed to cancel order: {order_id}")
                return None
                
        except Exception as e:
            error_msg = f"Error cancelling order: {str(e)}"
            log_error(
                logger,
                'CANCEL_ORDER_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'order_id': order_id
                }
            )
            return None
    
    def cancel_all_orders(self, symbol):
        """
        Cancel all open limit orders for symbol
        
        Args:
            symbol (str): Trading symbol
        
        Returns:
            dict: Cancel response or None if failed
        """
        try:
            response = self.client.cancel_all_orders(symbol)
            
            if response:
                logger.info(f"All orders cancelled for {symbol}")
                return response
            else:
                logger.error(f"Failed to cancel all orders for {symbol}")
                return None
                
        except Exception as e:
            error_msg = f"Error cancelling all orders: {str(e)}"
            log_error(
                logger,
                'CANCEL_ALL_ORDERS_ERROR',
                error_msg,
                {'symbol': symbol}
            )
            return None
    
    def get_open_orders(self, symbol=None):
        """
        Get open limit orders
        
        Args:
            symbol (str, optional): Trading symbol
        
        Returns:
            list: List of open orders
        """
        try:
            orders = self.client.get_open_orders(symbol)
            
            if orders is not None:
                # Filter only limit orders
                limit_orders = [order for order in orders if order.get('type') == 'LIMIT']
                logger.info(f"Retrieved {len(limit_orders)} open limit orders")
                return limit_orders
            else:
                logger.error("Failed to retrieve open orders")
                return []
                
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            return []
    
    def calculate_optimal_price(self, symbol, side, percentage_from_market=0.1):
        """
        Calculate optimal limit order price based on current market
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side ('BUY' or 'SELL')
            percentage_from_market (float): Percentage away from market price
        
        Returns:
            float: Optimal price or None if failed
        """
        try:
            # Get current market price
            ticker = self.client.get_ticker(symbol)
            
            if not ticker or 'price' not in ticker:
                logger.error(f"Could not get market price for {symbol}")
                return None
            
            market_price = float(ticker['price'])
            
            # Calculate optimal price based on side
            if side.upper() == 'BUY':
                # Buy limit should be below market price
                optimal_price = market_price * (1 - percentage_from_market / 100)
            else:  # SELL
                # Sell limit should be above market price
                optimal_price = market_price * (1 + percentage_from_market / 100)
            
            logger.info(f"Optimal {side} price for {symbol}: {optimal_price} (market: {market_price})")
            return optimal_price
            
        except Exception as e:
            logger.error(f"Error calculating optimal price: {str(e)}")
            return None
    
    def place_bracket_orders(self, symbol, quantity, entry_price, take_profit_price, stop_loss_price):
        """
        Place bracket orders (entry + take profit + stop loss)
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Order quantity
            entry_price (float): Entry limit price
            take_profit_price (float): Take profit price
            stop_loss_price (float): Stop loss price
        
        Returns:
            dict: Dictionary with order responses
        """
        try:
            orders = {}
            
            # Determine if this is a buy or sell bracket
            if take_profit_price > entry_price:
                # Buy bracket (long position)
                entry_side = 'BUY'
                tp_side = 'SELL'
                sl_side = 'SELL'
            else:
                # Sell bracket (short position)
                entry_side = 'SELL'
                tp_side = 'BUY'
                sl_side = 'BUY'
            
            # Place entry order
            entry_order = self.place_order(symbol, entry_side, quantity, entry_price)
            orders['entry'] = entry_order
            
            if entry_order:
                logger.info(f"Entry order placed: {entry_order.get('orderId')}")
                
                # Note: In a real implementation, you would wait for entry order to fill
                # before placing TP/SL orders, or use OCO orders
                # For simplicity, we're placing them immediately with reduce_only=True
                
                # Place take profit order
                tp_order = self.place_order(symbol, tp_side, quantity, take_profit_price, reduce_only=True)
                orders['take_profit'] = tp_order
                
                # Place stop loss order (would typically be a stop-limit order)
                sl_order = self.place_order(symbol, sl_side, quantity, stop_loss_price, reduce_only=True)
                orders['stop_loss'] = sl_order
                
                logger.info(f"Bracket orders placed for {symbol}")
            else:
                logger.error(f"Failed to place entry order for bracket")
            
            return orders
            
        except Exception as e:
            error_msg = f"Error placing bracket orders: {str(e)}"
            log_error(
                logger,
                'BRACKET_ORDER_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'take_profit_price': take_profit_price,
                    'stop_loss_price': stop_loss_price
                }
            )
            return {}
    
    def get_order_book_analysis(self, symbol, depth=10):
        """
        Analyze order book for limit order placement insights
        
        Args:
            symbol (str): Trading symbol
            depth (int): Order book depth to analyze
        
        Returns:
            dict: Order book analysis
        """
        try:
            orderbook = self.client.get_orderbook(symbol, limit=depth)
            
            if not orderbook:
                logger.error(f"Could not retrieve order book for {symbol}")
                return {}
            
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                logger.error(f"Empty order book for {symbol}")
                return {}
            
            # Convert to float and calculate metrics
            bid_prices = [float(bid[0]) for bid in bids]
            ask_prices = [float(ask[0]) for ask in asks]
            bid_volumes = [float(bid[1]) for bid in bids]
            ask_volumes = [float(ask[1]) for ask in asks]
            
            analysis = {
                'best_bid': bid_prices[0],
                'best_ask': ask_prices[0],
                'spread': ask_prices[0] - bid_prices[0],
                'spread_percentage': ((ask_prices[0] - bid_prices[0]) / bid_prices[0]) * 100,
                'bid_volume': sum(bid_volumes),
                'ask_volume': sum(ask_volumes),
                'volume_imbalance': (sum(bid_volumes) - sum(ask_volumes)) / (sum(bid_volumes) + sum(ask_volumes)),
                'mid_price': (bid_prices[0] + ask_prices[0]) / 2
            }
            
            logger.info(f"Order book analysis completed for {symbol}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing order book: {str(e)}")
            return {}
