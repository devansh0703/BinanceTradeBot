"""
TWAP (Time-Weighted Average Price) order handler
Splits large orders into smaller chunks executed over time
"""

import time
import threading
import math
from datetime import datetime, timedelta
from ..logger import setup_logger, log_trade, log_error
from ..market_orders import MarketOrderHandler

logger = setup_logger()

class TWAPOrderHandler:
    def __init__(self, binance_client):
        """
        Initialize TWAP order handler
        
        Args:
            binance_client: Binance API client instance
        """
        self.client = binance_client
        self.market_handler = MarketOrderHandler(binance_client)
        self.active_twaps = {}
        self.twap_counter = 0
        logger.info("TWAP order handler initialized")
    
    def start_twap(self, symbol, side, total_quantity, duration_minutes, intervals, 
                   order_type='MARKET', limit_price=None):
        """
        Start TWAP execution
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side ('BUY' or 'SELL')
            total_quantity (float): Total quantity to execute
            duration_minutes (int): Duration in minutes
            intervals (int): Number of intervals
            order_type (str): Order type ('MARKET' or 'LIMIT')
            limit_price (float, optional): Limit price for limit orders
        
        Returns:
            str: TWAP ID or None if failed
        """
        try:
            # Generate unique TWAP ID
            self.twap_counter += 1
            twap_id = f"TWAP_{self.twap_counter}_{int(time.time())}"
            
            # Calculate TWAP parameters
            quantity_per_interval = total_quantity / intervals
            interval_duration = duration_minutes / intervals
            
            # Create TWAP configuration
            twap_config = {
                'twap_id': twap_id,
                'symbol': symbol,
                'side': side,
                'total_quantity': total_quantity,
                'quantity_per_interval': quantity_per_interval,
                'duration_minutes': duration_minutes,
                'intervals': intervals,
                'interval_duration': interval_duration,
                'order_type': order_type,
                'limit_price': limit_price,
                'start_time': datetime.now(),
                'executed_quantity': 0,
                'executed_intervals': 0,
                'orders': [],
                'status': 'RUNNING',
                'stop_requested': False
            }
            
            # Store TWAP configuration
            self.active_twaps[twap_id] = twap_config
            
            # Log TWAP start
            log_trade(
                logger,
                'TWAP_START',
                symbol,
                side,
                total_quantity,
                price=limit_price,
                order_id=twap_id,
                status='STARTED'
            )
            
            # Start TWAP execution in separate thread
            twap_thread = threading.Thread(
                target=self._execute_twap,
                args=(twap_id,),
                daemon=True
            )
            twap_thread.start()
            
            logger.info(f"TWAP started: {twap_id} - {total_quantity} {symbol} over {duration_minutes}m")
            return twap_id
            
        except Exception as e:
            error_msg = f"Error starting TWAP: {str(e)}"
            log_error(
                logger,
                'TWAP_START_ERROR',
                error_msg,
                {
                    'symbol': symbol,
                    'side': side,
                    'total_quantity': total_quantity,
                    'duration_minutes': duration_minutes,
                    'intervals': intervals
                }
            )
            return None
    
    def _execute_twap(self, twap_id):
        """
        Execute TWAP strategy
        
        Args:
            twap_id (str): TWAP identifier
        """
        try:
            twap_config = self.active_twaps.get(twap_id)
            if not twap_config:
                logger.error(f"TWAP configuration not found: {twap_id}")
                return
            
            symbol = twap_config['symbol']
            side = twap_config['side']
            quantity_per_interval = twap_config['quantity_per_interval']
            interval_duration_seconds = twap_config['interval_duration'] * 60
            order_type = twap_config['order_type']
            limit_price = twap_config['limit_price']
            
            logger.info(f"Executing TWAP {twap_id}: {twap_config['intervals']} intervals")
            
            for interval in range(twap_config['intervals']):
                # Check if stop was requested
                if twap_config['stop_requested']:
                    logger.info(f"TWAP {twap_id} stopped by request")
                    break
                
                try:
                    # Execute order for this interval
                    if order_type == 'MARKET':
                        order_response = self.market_handler.place_order(
                            symbol, side, quantity_per_interval
                        )
                    else:  # LIMIT
                        # For limit orders, we could use current market price + spread
                        current_price = self._get_adaptive_price(symbol, side, limit_price)
                        order_response = self._place_limit_order(
                            symbol, side, quantity_per_interval, current_price
                        )
                    
                    if order_response:
                        # Update TWAP status
                        twap_config['executed_quantity'] += quantity_per_interval
                        twap_config['executed_intervals'] += 1
                        twap_config['orders'].append(order_response)
                        
                        logger.info(f"TWAP {twap_id} interval {interval + 1} executed: {quantity_per_interval}")
                    else:
                        logger.error(f"TWAP {twap_id} interval {interval + 1} failed")
                    
                    # Wait for next interval (except for last one)
                    if interval < twap_config['intervals'] - 1:
                        time.sleep(interval_duration_seconds)
                        
                except Exception as e:
                    logger.error(f"Error in TWAP interval {interval + 1}: {str(e)}")
                    continue
            
            # Mark TWAP as completed
            twap_config['status'] = 'COMPLETED'
            twap_config['end_time'] = datetime.now()
            
            # Log completion
            log_trade(
                logger,
                'TWAP_COMPLETE',
                symbol,
                side,
                twap_config['executed_quantity'],
                order_id=twap_id,
                status='COMPLETED'
            )
            
            logger.info(f"TWAP {twap_id} completed: {twap_config['executed_quantity']}/{twap_config['total_quantity']}")
            
        except Exception as e:
            error_msg = f"Error executing TWAP {twap_id}: {str(e)}"
            log_error(logger, 'TWAP_EXECUTION_ERROR', error_msg, {'twap_id': twap_id})
            
            # Mark as failed
            if twap_id in self.active_twaps:
                self.active_twaps[twap_id]['status'] = 'FAILED'
    
    def _get_adaptive_price(self, symbol, side, base_price):
        """
        Get adaptive price based on current market conditions
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side
            base_price (float): Base price
        
        Returns:
            float: Adaptive price
        """
        try:
            # Get current market price
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                return base_price
            
            market_price = float(ticker['price'])
            
            # Adjust price based on market movement
            if side == 'BUY':
                # For buy orders, use slightly above market to ensure execution
                adaptive_price = min(base_price, market_price * 1.001)
            else:  # SELL
                # For sell orders, use slightly below market to ensure execution
                adaptive_price = max(base_price, market_price * 0.999)
            
            return adaptive_price
            
        except Exception as e:
            logger.error(f"Error getting adaptive price: {str(e)}")
            return base_price
    
    def _place_limit_order(self, symbol, side, quantity, price):
        """
        Place limit order for TWAP interval
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side
            quantity (float): Order quantity
            price (float): Limit price
        
        Returns:
            dict: Order response
        """
        try:
            return self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='IOC'  # Immediate or Cancel for TWAP
            )
        except Exception as e:
            logger.error(f"Error placing TWAP limit order: {str(e)}")
            return None
    
    def stop_twap(self, twap_id):
        """
        Stop running TWAP
        
        Args:
            twap_id (str): TWAP identifier
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            if twap_id not in self.active_twaps:
                logger.error(f"TWAP not found: {twap_id}")
                return False
            
            twap_config = self.active_twaps[twap_id]
            twap_config['stop_requested'] = True
            twap_config['status'] = 'STOPPED'
            
            logger.info(f"TWAP stop requested: {twap_id}")
            
            # Log stop
            log_trade(
                logger,
                'TWAP_STOP',
                twap_config['symbol'],
                twap_config['side'],
                twap_config['executed_quantity'],
                order_id=twap_id,
                status='STOPPED'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping TWAP: {str(e)}")
            return False
    
    def get_twap_status(self, twap_id):
        """
        Get TWAP status
        
        Args:
            twap_id (str): TWAP identifier
        
        Returns:
            dict: TWAP status information
        """
        try:
            if twap_id not in self.active_twaps:
                return None
            
            twap_config = self.active_twaps[twap_id]
            
            # Calculate progress
            progress_percentage = (twap_config['executed_intervals'] / twap_config['intervals']) * 100
            quantity_percentage = (twap_config['executed_quantity'] / twap_config['total_quantity']) * 100
            
            # Calculate VWAP (Volume Weighted Average Price)
            vwap = self._calculate_vwap(twap_config['orders'])
            
            status_info = {
                'twap_id': twap_id,
                'status': twap_config['status'],
                'symbol': twap_config['symbol'],
                'side': twap_config['side'],
                'total_quantity': twap_config['total_quantity'],
                'executed_quantity': twap_config['executed_quantity'],
                'remaining_quantity': twap_config['total_quantity'] - twap_config['executed_quantity'],
                'progress_percentage': progress_percentage,
                'quantity_percentage': quantity_percentage,
                'executed_intervals': twap_config['executed_intervals'],
                'total_intervals': twap_config['intervals'],
                'vwap': vwap,
                'start_time': twap_config['start_time'],
                'orders_count': len(twap_config['orders'])
            }
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting TWAP status: {str(e)}")
            return None
    
    def _calculate_vwap(self, orders):
        """
        Calculate Volume Weighted Average Price from executed orders
        
        Args:
            orders (list): List of executed orders
        
        Returns:
            float: VWAP or None if no orders
        """
        try:
            if not orders:
                return None
            
            total_value = 0
            total_quantity = 0
            
            for order in orders:
                if order and 'price' in order and 'executedQty' in order:
                    price = float(order['price'])
                    quantity = float(order['executedQty'])
                    total_value += price * quantity
                    total_quantity += quantity
            
            if total_quantity > 0:
                return total_value / total_quantity
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error calculating VWAP: {str(e)}")
            return None
    
    def get_all_active_twaps(self):
        """
        Get all active TWAP orders
        
        Returns:
            dict: Dictionary of active TWAP orders
        """
        try:
            active_twaps = {}
            
            for twap_id, config in self.active_twaps.items():
                if config['status'] in ['RUNNING', 'STOPPED']:
                    active_twaps[twap_id] = self.get_twap_status(twap_id)
            
            return active_twaps
            
        except Exception as e:
            logger.error(f"Error getting active TWAPs: {str(e)}")
            return {}
    
    def cleanup_completed_twaps(self):
        """
        Clean up completed TWAP orders from memory
        
        Returns:
            int: Number of TWAPs cleaned up
        """
        try:
            completed_twaps = []
            
            for twap_id, config in self.active_twaps.items():
                if config['status'] in ['COMPLETED', 'FAILED']:
                    # Keep completed TWAPs for a while before cleanup
                    if 'end_time' in config:
                        time_diff = datetime.now() - config['end_time']
                        if time_diff > timedelta(hours=1):  # Clean up after 1 hour
                            completed_twaps.append(twap_id)
            
            # Remove completed TWAPs
            for twap_id in completed_twaps:
                del self.active_twaps[twap_id]
                logger.info(f"Cleaned up completed TWAP: {twap_id}")
            
            return len(completed_twaps)
            
        except Exception as e:
            logger.error(f"Error cleaning up TWAPs: {str(e)}")
            return 0
    
    def calculate_twap_performance(self, twap_id):
        """
        Calculate TWAP performance metrics
        
        Args:
            twap_id (str): TWAP identifier
        
        Returns:
            dict: Performance metrics
        """
        try:
            if twap_id not in self.active_twaps:
                return {}
            
            twap_config = self.active_twaps[twap_id]
            orders = twap_config['orders']
            
            if not orders:
                return {}
            
            # Calculate metrics
            vwap = self._calculate_vwap(orders)
            
            # Get benchmark price (first order price)
            benchmark_price = None
            if orders and 'price' in orders[0]:
                benchmark_price = float(orders[0]['price'])
            
            # Calculate slippage
            slippage = 0
            if vwap and benchmark_price:
                slippage = ((vwap - benchmark_price) / benchmark_price) * 100
            
            # Calculate execution time
            execution_time = 0
            if 'end_time' in twap_config:
                execution_time = (twap_config['end_time'] - twap_config['start_time']).total_seconds()
            
            performance = {
                'twap_id': twap_id,
                'vwap': vwap,
                'benchmark_price': benchmark_price,
                'slippage_percentage': slippage,
                'execution_time_seconds': execution_time,
                'orders_executed': len(orders),
                'average_order_size': twap_config['executed_quantity'] / len(orders) if orders else 0,
                'completion_rate': (twap_config['executed_quantity'] / twap_config['total_quantity']) * 100
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"Error calculating TWAP performance: {str(e)}")
            return {}
