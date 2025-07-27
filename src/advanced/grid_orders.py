"""
Grid trading order handler
Implements automated buy-low/sell-high strategy within a price range
"""

import time
import threading
import math
from datetime import datetime
from ..logger import setup_logger, log_trade, log_error

logger = setup_logger()

class GridOrderHandler:
    def __init__(self, binance_client):
        """
        Initialize Grid trading handler
        
        Args:
            binance_client: Binance API client instance
        """
        self.client = binance_client
        self.active_grids = {}
        self.grid_counter = 0
        self.monitoring_threads = {}
        logger.info("Grid trading handler initialized")
    
    def start_grid(self, symbol, upper_price, lower_price, grid_levels, total_quantity,
                   grid_type='NEUTRAL', take_profit_percentage=None):
        """
        Start grid trading strategy
        
        Args:
            symbol (str): Trading symbol
            upper_price (float): Upper price bound
            lower_price (float): Lower price bound
            grid_levels (int): Number of grid levels
            total_quantity (float): Total quantity to allocate
            grid_type (str): Grid type ('NEUTRAL', 'LONG', 'SHORT')
            take_profit_percentage (float, optional): Take profit percentage
        
        Returns:
            str: Grid ID or None if failed
        """
        try:
            # Generate unique grid ID
            self.grid_counter += 1
            grid_id = f"GRID_{self.grid_counter}_{int(time.time())}"
            
            # Calculate grid parameters
            price_increment = (upper_price - lower_price) / (grid_levels - 1)
            quantity_per_level = total_quantity / grid_levels
            
            # Create grid levels
            grid_levels_data = []
            for i in range(grid_levels):
                level_price = lower_price + (i * price_increment)
                grid_levels_data.append({
                    'level': i,
                    'price': level_price,
                    'quantity': quantity_per_level,
                    'buy_order_id': None,
                    'sell_order_id': None,
                    'filled': False
                })
            
            # Create grid configuration
            grid_config = {
                'grid_id': grid_id,
                'symbol': symbol,
                'upper_price': upper_price,
                'lower_price': lower_price,
                'grid_levels': grid_levels,
                'total_quantity': total_quantity,
                'quantity_per_level': quantity_per_level,
                'price_increment': price_increment,
                'grid_type': grid_type,
                'take_profit_percentage': take_profit_percentage,
                'levels': grid_levels_data,
                'start_time': datetime.now(),
                'status': 'ACTIVE',
                'total_profit': 0,
                'trades_executed': 0,
                'stop_requested': False
            }
            
            # Store grid configuration
            self.active_grids[grid_id] = grid_config
            
            # Log grid start
            log_trade(
                logger,
                'GRID_START',
                symbol,
                'GRID',
                total_quantity,
                order_id=grid_id,
                status='STARTED'
            )
            
            # Place initial grid orders
            success = self._place_initial_grid_orders(grid_id)
            
            if success:
                # Start monitoring thread
                monitor_thread = threading.Thread(
                    target=self._monitor_grid,
                    args=(grid_id,),
                    daemon=True
                )
                monitor_thread.start()
                self.monitoring_threads[grid_id] = monitor_thread
                
                logger.info(f"Grid trading started: {grid_id} - {symbol} with {grid_levels} levels")
                return grid_id
            else:
                # Clean up if initial orders failed
                del self.active_grids[grid_id]
                logger.error(f"Failed to place initial grid orders for {grid_id}")
                return None
                
        except Exception as e:
            error_msg = f"Error starting grid trading: {str(e)}"
            log_error(
                logger,
                'GRID_START_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'upper_price': upper_price,
                    'lower_price': lower_price,
                    'grid_levels': grid_levels,
                    'total_quantity': total_quantity
                }
            )
            return None
    
    def _place_initial_grid_orders(self, grid_id):
        """
        Place initial grid orders
        
        Args:
            grid_id (str): Grid identifier
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            grid_config = self.active_grids[grid_id]
            symbol = grid_config['symbol']
            grid_type = grid_config['grid_type']
            
            # Get current market price
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                logger.error(f"Could not get market price for {symbol}")
                return False
            
            current_price = float(ticker['price'])
            
            successful_orders = 0
            total_orders_attempted = 0
            
            for level_data in grid_config['levels']:
                level_price = level_data['price']
                quantity = level_data['quantity']
                
                try:
                    # Determine which orders to place based on current price and grid type
                    if grid_type == 'NEUTRAL':
                        # Place both buy and sell orders
                        if level_price < current_price:
                            # Place buy order below current price
                            buy_order = self._place_grid_order(symbol, 'BUY', quantity, level_price)
                            if buy_order:
                                level_data['buy_order_id'] = buy_order.get('orderId')
                                successful_orders += 1
                            total_orders_attempted += 1
                        
                        if level_price > current_price:
                            # Place sell order above current price
                            sell_order = self._place_grid_order(symbol, 'SELL', quantity, level_price)
                            if sell_order:
                                level_data['sell_order_id'] = sell_order.get('orderId')
                                successful_orders += 1
                            total_orders_attempted += 1
                    
                    elif grid_type == 'LONG':
                        # Only place buy orders (accumulation strategy)
                        if level_price <= current_price:
                            buy_order = self._place_grid_order(symbol, 'BUY', quantity, level_price)
                            if buy_order:
                                level_data['buy_order_id'] = buy_order.get('orderId')
                                successful_orders += 1
                            total_orders_attempted += 1
                    
                    elif grid_type == 'SHORT':
                        # Only place sell orders (distribution strategy)
                        if level_price >= current_price:
                            sell_order = self._place_grid_order(symbol, 'SELL', quantity, level_price)
                            if sell_order:
                                level_data['sell_order_id'] = sell_order.get('orderId')
                                successful_orders += 1
                            total_orders_attempted += 1
                    
                except Exception as e:
                    logger.error(f"Error placing order for grid level {level_data['level']}: {str(e)}")
                    continue
            
            success_rate = successful_orders / total_orders_attempted if total_orders_attempted > 0 else 0
            logger.info(f"Grid initial orders: {successful_orders}/{total_orders_attempted} successful ({success_rate:.1%})")
            
            return success_rate >= 0.7  # Consider successful if 70% of orders placed
            
        except Exception as e:
            logger.error(f"Error placing initial grid orders: {str(e)}")
            return False
    
    def _place_grid_order(self, symbol, side, quantity, price):
        """
        Place individual grid order
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side
            quantity (float): Order quantity
            price (float): Order price
        
        Returns:
            dict: Order response or None
        """
        try:
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTC'
            )
            
            if response:
                logger.debug(f"Grid order placed: {side} {quantity} {symbol} @ {price}")
                return response
            else:
                logger.error(f"Failed to place grid order: {side} {quantity} {symbol} @ {price}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing grid order: {str(e)}")
            return None
    
    def _monitor_grid(self, grid_id):
        """
        Monitor grid orders and manage fills
        
        Args:
            grid_id (str): Grid identifier
        """
        try:
            grid_config = self.active_grids.get(grid_id)
            if not grid_config:
                return
            
            symbol = grid_config['symbol']
            logger.info(f"Grid monitoring started for {grid_id}")
            
            while grid_config.get('status') == 'ACTIVE' and not grid_config.get('stop_requested'):
                try:
                    # Check order status for each level
                    for level_data in grid_config['levels']:
                        self._check_level_orders(grid_id, level_data)
                    
                    # Check take profit conditions
                    if grid_config.get('take_profit_percentage'):
                        self._check_take_profit(grid_id)
                    
                    time.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Error in grid monitoring iteration: {str(e)}")
                    continue
            
            logger.info(f"Grid monitoring stopped for {grid_id}")
            
        except Exception as e:
            logger.error(f"Error in grid monitoring: {str(e)}")
        finally:
            # Clean up monitoring thread reference
            if grid_id in self.monitoring_threads:
                del self.monitoring_threads[grid_id]
    
    def _check_level_orders(self, grid_id, level_data):
        """
        Check status of orders for a specific grid level
        
        Args:
            grid_id (str): Grid identifier
            level_data (dict): Level data
        """
        try:
            grid_config = self.active_grids[grid_id]
            symbol = grid_config['symbol']
            
            # Check buy order
            if level_data['buy_order_id']:
                buy_status = self.client.get_order_status(symbol, order_id=level_data['buy_order_id'])
                if buy_status and buy_status.get('status') == 'FILLED':
                    self._handle_buy_fill(grid_id, level_data)
            
            # Check sell order
            if level_data['sell_order_id']:
                sell_status = self.client.get_order_status(symbol, order_id=level_data['sell_order_id'])
                if sell_status and sell_status.get('status') == 'FILLED':
                    self._handle_sell_fill(grid_id, level_data)
                    
        except Exception as e:
            logger.error(f"Error checking level orders: {str(e)}")
    
    def _handle_buy_fill(self, grid_id, level_data):
        """
        Handle buy order fill
        
        Args:
            grid_id (str): Grid identifier
            level_data (dict): Level data
        """
        try:
            grid_config = self.active_grids[grid_id]
            symbol = grid_config['symbol']
            
            logger.info(f"Grid buy order filled: Level {level_data['level']} @ {level_data['price']}")
            
            # Mark level as filled
            level_data['filled'] = True
            grid_config['trades_executed'] += 1
            
            # Place corresponding sell order at next level up
            next_level_index = level_data['level'] + 1
            if next_level_index < len(grid_config['levels']):
                next_level = grid_config['levels'][next_level_index]
                if not next_level['sell_order_id']:
                    sell_order = self._place_grid_order(
                        symbol, 'SELL', level_data['quantity'], next_level['price']
                    )
                    if sell_order:
                        next_level['sell_order_id'] = sell_order.get('orderId')
            
            # Clear buy order ID
            level_data['buy_order_id'] = None
            
        except Exception as e:
            logger.error(f"Error handling buy fill: {str(e)}")
    
    def _handle_sell_fill(self, grid_id, level_data):
        """
        Handle sell order fill
        
        Args:
            grid_id (str): Grid identifier
            level_data (dict): Level data
        """
        try:
            grid_config = self.active_grids[grid_id]
            symbol = grid_config['symbol']
            
            logger.info(f"Grid sell order filled: Level {level_data['level']} @ {level_data['price']}")
            
            # Calculate profit
            price_increment = grid_config['price_increment']
            quantity = level_data['quantity']
            profit = price_increment * quantity
            grid_config['total_profit'] += profit
            grid_config['trades_executed'] += 1
            
            # Mark level as filled
            level_data['filled'] = True
            
            # Place corresponding buy order at next level down
            prev_level_index = level_data['level'] - 1
            if prev_level_index >= 0:
                prev_level = grid_config['levels'][prev_level_index]
                if not prev_level['buy_order_id']:
                    buy_order = self._place_grid_order(
                        symbol, 'BUY', level_data['quantity'], prev_level['price']
                    )
                    if buy_order:
                        prev_level['buy_order_id'] = buy_order.get('orderId')
            
            # Clear sell order ID
            level_data['sell_order_id'] = None
            
            log_trade(
                logger,
                'GRID_PROFIT',
                symbol,
                'SELL',
                quantity,
                price=level_data['price'],
                order_id=grid_id,
                status='PROFIT_REALIZED'
            )
            
        except Exception as e:
            logger.error(f"Error handling sell fill: {str(e)}")
    
    def _check_take_profit(self, grid_id):
        """
        Check take profit conditions
        
        Args:
            grid_id (str): Grid identifier
        """
        try:
            grid_config = self.active_grids[grid_id]
            take_profit_percentage = grid_config.get('take_profit_percentage')
            
            if not take_profit_percentage:
                return
            
            # Calculate profit percentage
            total_investment = grid_config['total_quantity'] * grid_config['lower_price']
            profit_percentage = (grid_config['total_profit'] / total_investment) * 100
            
            if profit_percentage >= take_profit_percentage:
                logger.info(f"Take profit triggered for grid {grid_id}: {profit_percentage:.2f}%")
                self.stop_grid(grid_id, reason='TAKE_PROFIT')
                
        except Exception as e:
            logger.error(f"Error checking take profit: {str(e)}")
    
    def stop_grid(self, grid_id, reason='MANUAL'):
        """
        Stop grid trading
        
        Args:
            grid_id (str): Grid identifier
            reason (str): Reason for stopping
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            if grid_id not in self.active_grids:
                logger.error(f"Grid not found: {grid_id}")
                return False
            
            grid_config = self.active_grids[grid_id]
            grid_config['stop_requested'] = True
            grid_config['status'] = 'STOPPING'
            
            symbol = grid_config['symbol']
            
            # Cancel all open orders
            cancelled_orders = 0
            for level_data in grid_config['levels']:
                if level_data['buy_order_id']:
                    cancel_response = self.client.cancel_order(symbol, order_id=level_data['buy_order_id'])
                    if cancel_response:
                        cancelled_orders += 1
                    level_data['buy_order_id'] = None
                
                if level_data['sell_order_id']:
                    cancel_response = self.client.cancel_order(symbol, order_id=level_data['sell_order_id'])
                    if cancel_response:
                        cancelled_orders += 1
                    level_data['sell_order_id'] = None
            
            grid_config['status'] = 'STOPPED'
            grid_config['stop_time'] = datetime.now()
            grid_config['stop_reason'] = reason
            
            logger.info(f"Grid {grid_id} stopped ({reason}): {cancelled_orders} orders cancelled")
            
            # Log grid stop
            log_trade(
                logger,
                'GRID_STOP',
                symbol,
                'GRID',
                grid_config['total_quantity'],
                order_id=grid_id,
                status=f'STOPPED_{reason}'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping grid: {str(e)}")
            return False
    
    def get_grid_status(self, grid_id):
        """
        Get grid status information
        
        Args:
            grid_id (str): Grid identifier
        
        Returns:
            dict: Grid status information
        """
        try:
            if grid_id not in self.active_grids:
                return None
            
            grid_config = self.active_grids[grid_id]
            
            # Calculate statistics
            active_buy_orders = sum(1 for level in grid_config['levels'] if level['buy_order_id'])
            active_sell_orders = sum(1 for level in grid_config['levels'] if level['sell_order_id'])
            filled_levels = sum(1 for level in grid_config['levels'] if level['filled'])
            
            # Calculate profit percentage
            total_investment = grid_config['total_quantity'] * grid_config['lower_price']
            profit_percentage = (grid_config['total_profit'] / total_investment) * 100 if total_investment > 0 else 0
            
            # Calculate runtime
            runtime = datetime.now() - grid_config['start_time']
            
            status_info = {
                'grid_id': grid_id,
                'symbol': grid_config['symbol'],
                'status': grid_config['status'],
                'grid_type': grid_config['grid_type'],
                'upper_price': grid_config['upper_price'],
                'lower_price': grid_config['lower_price'],
                'grid_levels': grid_config['grid_levels'],
                'total_quantity': grid_config['total_quantity'],
                'total_profit': grid_config['total_profit'],
                'profit_percentage': profit_percentage,
                'trades_executed': grid_config['trades_executed'],
                'active_buy_orders': active_buy_orders,
                'active_sell_orders': active_sell_orders,
                'filled_levels': filled_levels,
                'runtime_seconds': runtime.total_seconds(),
                'start_time': grid_config['start_time']
            }
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting grid status: {str(e)}")
            return None
    
    def get_all_active_grids(self):
        """
        Get all active grids
        
        Returns:
            dict: Dictionary of active grids
        """
        try:
            active_grids = {}
            
            for grid_id in self.active_grids:
                status = self.get_grid_status(grid_id)
                if status and status['status'] in ['ACTIVE', 'STOPPING']:
                    active_grids[grid_id] = status
            
            return active_grids
            
        except Exception as e:
            logger.error(f"Error getting active grids: {str(e)}")
            return {}
    
    def calculate_optimal_grid_parameters(self, symbol, timeframe='1d', lookback_days=30):
        """
        Calculate optimal grid parameters based on historical data
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe for analysis
            lookback_days (int): Number of days to look back
        
        Returns:
            dict: Optimal grid parameters
        """
        try:
            # Get historical data
            end_time = int(time.time() * 1000)
            start_time = end_time - (lookback_days * 24 * 60 * 60 * 1000)
            
            klines = self.client.get_klines(
                symbol, timeframe, limit=1000, start_time=start_time, end_time=end_time
            )
            
            if not klines:
                logger.error(f"No historical data for {symbol}")
                return {}
            
            # Extract price data
            highs = [float(kline[2]) for kline in klines]
            lows = [float(kline[3]) for kline in klines]
            closes = [float(kline[4]) for kline in klines]
            
            # Calculate statistics
            max_price = max(highs)
            min_price = min(lows)
            avg_price = sum(closes) / len(closes)
            price_range = max_price - min_price
            
            # Calculate volatility
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5
            
            # Suggest grid parameters
            suggested_upper = avg_price + (price_range * 0.3)
            suggested_lower = avg_price - (price_range * 0.3)
            suggested_levels = max(5, min(20, int(volatility * 100)))
            
            parameters = {
                'symbol': symbol,
                'historical_max': max_price,
                'historical_min': min_price,
                'average_price': avg_price,
                'price_range': price_range,
                'volatility': volatility,
                'suggested_upper_price': suggested_upper,
                'suggested_lower_price': suggested_lower,
                'suggested_grid_levels': suggested_levels,
                'analysis_period': f"{lookback_days} days"
            }
            
            logger.info(f"Optimal grid parameters calculated for {symbol}")
            return parameters
            
        except Exception as e:
            logger.error(f"Error calculating optimal grid parameters: {str(e)}")
            return {}
    
    def cleanup_stopped_grids(self):
        """
        Clean up stopped grids from memory
        
        Returns:
            int: Number of grids cleaned up
        """
        try:
            stopped_grids = []
            
            for grid_id, config in self.active_grids.items():
                if config['status'] == 'STOPPED':
                    # Keep stopped grids for a while before cleanup
                    if 'stop_time' in config:
                        time_diff = datetime.now() - config['stop_time']
                        if time_diff.total_seconds() > 3600:  # Clean up after 1 hour
                            stopped_grids.append(grid_id)
            
            # Remove stopped grids
            for grid_id in stopped_grids:
                del self.active_grids[grid_id]
                logger.info(f"Cleaned up stopped grid: {grid_id}")
            
            return len(stopped_grids)
            
        except Exception as e:
            logger.error(f"Error cleaning up grids: {str(e)}")
            return 0
