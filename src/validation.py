"""
Input validation module for trading parameters
"""

import re
from decimal import Decimal, InvalidOperation
from .logger import setup_logger

logger = setup_logger()

class Validator:
    def __init__(self):
        """Initialize validator with trading rules"""
        self.valid_symbols = {
            'BTCUSDT': {'min_qty': 0.001, 'max_qty': 1000, 'tick_size': 0.01},
            'ETHUSDT': {'min_qty': 0.001, 'max_qty': 10000, 'tick_size': 0.01},
            'ADAUSDT': {'min_qty': 1, 'max_qty': 1000000, 'tick_size': 0.0001},
            'SOLUSDT': {'min_qty': 0.01, 'max_qty': 100000, 'tick_size': 0.001},
            'DOTUSDT': {'min_qty': 0.1, 'max_qty': 100000, 'tick_size': 0.001}
        }
        
        self.valid_sides = ['BUY', 'SELL']
        self.valid_order_types = ['MARKET', 'LIMIT', 'STOP', 'STOP_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_MARKET']
        self.valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        
        logger.info("Validator initialized with trading rules")
    
    def validate_symbol(self, symbol):
        """
        Validate trading symbol
        
        Args:
            symbol (str): Trading symbol
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(symbol, str):
            logger.error(f"Invalid symbol type: {type(symbol)}")
            return False
        
        symbol = symbol.upper().strip()
        
        if symbol not in self.valid_symbols:
            logger.error(f"Invalid symbol: {symbol}")
            return False
        
        return True
    
    def validate_quantity(self, symbol, quantity):
        """
        Validate trade quantity
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Trade quantity
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.validate_symbol(symbol):
            return False
        
        try:
            quantity = float(quantity)
        except (ValueError, TypeError):
            logger.error(f"Invalid quantity type: {quantity}")
            return False
        
        if quantity <= 0:
            logger.error(f"Quantity must be positive: {quantity}")
            return False
        
        symbol_rules = self.valid_symbols[symbol.upper()]
        
        if quantity < symbol_rules['min_qty']:
            logger.error(f"Quantity below minimum for {symbol}: {quantity} < {symbol_rules['min_qty']}")
            return False
        
        if quantity > symbol_rules['max_qty']:
            logger.error(f"Quantity above maximum for {symbol}: {quantity} > {symbol_rules['max_qty']}")
            return False
        
        return True
    
    def validate_price(self, symbol, price):
        """
        Validate price
        
        Args:
            symbol (str): Trading symbol
            price (float): Price
        
        Returns:
            bool: True if valid, False otherwise
        """
        if price is None:
            return True  # Price can be None for market orders
        
        if not self.validate_symbol(symbol):
            return False
        
        try:
            price = float(price)
        except (ValueError, TypeError):
            logger.error(f"Invalid price type: {price}")
            return False
        
        if price <= 0:
            logger.error(f"Price must be positive: {price}")
            return False
        
        # Check tick size
        symbol_rules = self.valid_symbols[symbol.upper()]
        tick_size = symbol_rules['tick_size']
        
        # Round to tick size and check if it matches
        rounded_price = round(price / tick_size) * tick_size
        if abs(price - rounded_price) > tick_size * 0.001:  # Small tolerance for floating point
            logger.error(f"Price {price} doesn't match tick size {tick_size} for {symbol}")
            return False
        
        return True
    
    def validate_side(self, side):
        """
        Validate order side
        
        Args:
            side (str): Order side (BUY or SELL)
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(side, str):
            logger.error(f"Invalid side type: {type(side)}")
            return False
        
        side = side.upper().strip()
        
        if side not in self.valid_sides:
            logger.error(f"Invalid side: {side}")
            return False
        
        return True
    
    def validate_order_type(self, order_type):
        """
        Validate order type
        
        Args:
            order_type (str): Order type
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(order_type, str):
            logger.error(f"Invalid order type type: {type(order_type)}")
            return False
        
        order_type = order_type.upper().strip()
        
        if order_type not in self.valid_order_types:
            logger.error(f"Invalid order type: {order_type}")
            return False
        
        return True
    
    def validate_timeframe(self, timeframe):
        """
        Validate timeframe
        
        Args:
            timeframe (str): Timeframe
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(timeframe, str):
            logger.error(f"Invalid timeframe type: {type(timeframe)}")
            return False
        
        timeframe = timeframe.lower().strip()
        
        if timeframe not in self.valid_timeframes:
            logger.error(f"Invalid timeframe: {timeframe}")
            return False
        
        return True
    
    def validate_leverage(self, leverage):
        """
        Validate leverage
        
        Args:
            leverage (int): Leverage value
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            leverage = int(leverage)
        except (ValueError, TypeError):
            logger.error(f"Invalid leverage type: {leverage}")
            return False
        
        if leverage < 1 or leverage > 125:
            logger.error(f"Leverage must be between 1 and 125: {leverage}")
            return False
        
        return True
    
    def validate_order(self, symbol, quantity, price=None, side='BUY', order_type='MARKET'):
        """
        Validate complete order parameters
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Trade quantity
            price (float, optional): Price for limit orders
            side (str): Order side
            order_type (str): Order type
        
        Returns:
            bool: True if all parameters are valid, False otherwise
        """
        validations = [
            self.validate_symbol(symbol),
            self.validate_quantity(symbol, quantity),
            self.validate_price(symbol, price),
            self.validate_side(side),
            self.validate_order_type(order_type)
        ]
        
        # Special validation for limit orders
        if order_type.upper() in ['LIMIT', 'STOP_LIMIT'] and price is None:
            logger.error(f"Price required for {order_type} orders")
            return False
        
        is_valid = all(validations)
        
        if is_valid:
            logger.info(f"Order validation passed: {order_type} {side} {quantity} {symbol}")
        else:
            logger.error(f"Order validation failed: {order_type} {side} {quantity} {symbol}")
        
        return is_valid
    
    def validate_oco_order(self, symbol, quantity, price, stop_price, stop_limit_price, side='SELL'):
        """
        Validate OCO (One-Cancels-Other) order parameters
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Trade quantity
            price (float): Limit order price
            stop_price (float): Stop price
            stop_limit_price (float): Stop limit price
            side (str): Order side
        
        Returns:
            bool: True if valid, False otherwise
        """
        basic_validations = [
            self.validate_symbol(symbol),
            self.validate_quantity(symbol, quantity),
            self.validate_price(symbol, price),
            self.validate_price(symbol, stop_price),
            self.validate_price(symbol, stop_limit_price),
            self.validate_side(side)
        ]
        
        if not all(basic_validations):
            return False
        
        # OCO specific validations
        if side.upper() == 'SELL':
            # For sell OCO: limit price > current price, stop price < current price
            if stop_price >= price:
                logger.error(f"For SELL OCO, stop price must be less than limit price: {stop_price} >= {price}")
                return False
            
            if stop_limit_price > stop_price:
                logger.error(f"For SELL OCO, stop limit price must be <= stop price: {stop_limit_price} > {stop_price}")
                return False
        
        elif side.upper() == 'BUY':
            # For buy OCO: limit price < current price, stop price > current price
            if stop_price <= price:
                logger.error(f"For BUY OCO, stop price must be greater than limit price: {stop_price} <= {price}")
                return False
            
            if stop_limit_price < stop_price:
                logger.error(f"For BUY OCO, stop limit price must be >= stop price: {stop_limit_price} < {stop_price}")
                return False
        
        logger.info(f"OCO order validation passed: {side} {quantity} {symbol}")
        return True
    
    def validate_twap_parameters(self, total_quantity, duration_minutes, intervals):
        """
        Validate TWAP order parameters
        
        Args:
            total_quantity (float): Total quantity to trade
            duration_minutes (int): Duration in minutes
            intervals (int): Number of intervals
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            total_quantity = float(total_quantity)
            duration_minutes = int(duration_minutes)
            intervals = int(intervals)
        except (ValueError, TypeError):
            logger.error("Invalid TWAP parameter types")
            return False
        
        if total_quantity <= 0:
            logger.error(f"Total quantity must be positive: {total_quantity}")
            return False
        
        if duration_minutes < 1:
            logger.error(f"Duration must be at least 1 minute: {duration_minutes}")
            return False
        
        if intervals < 2:
            logger.error(f"Intervals must be at least 2: {intervals}")
            return False
        
        if intervals > duration_minutes:
            logger.error(f"Intervals cannot exceed duration: {intervals} > {duration_minutes}")
            return False
        
        # Check if quantity per interval is valid
        quantity_per_interval = total_quantity / intervals
        if quantity_per_interval <= 0:
            logger.error(f"Quantity per interval too small: {quantity_per_interval}")
            return False
        
        logger.info(f"TWAP validation passed: {total_quantity} over {duration_minutes}m in {intervals} intervals")
        return True
    
    def validate_grid_parameters(self, upper_price, lower_price, grid_levels, total_quantity):
        """
        Validate Grid trading parameters
        
        Args:
            upper_price (float): Upper price bound
            lower_price (float): Lower price bound
            grid_levels (int): Number of grid levels
            total_quantity (float): Total quantity
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            upper_price = float(upper_price)
            lower_price = float(lower_price)
            grid_levels = int(grid_levels)
            total_quantity = float(total_quantity)
        except (ValueError, TypeError):
            logger.error("Invalid grid parameter types")
            return False
        
        if upper_price <= lower_price:
            logger.error(f"Upper price must be greater than lower price: {upper_price} <= {lower_price}")
            return False
        
        if grid_levels < 3:
            logger.error(f"Grid levels must be at least 3: {grid_levels}")
            return False
        
        if grid_levels > 50:
            logger.error(f"Grid levels cannot exceed 50: {grid_levels}")
            return False
        
        if total_quantity <= 0:
            logger.error(f"Total quantity must be positive: {total_quantity}")
            return False
        
        # Check price difference per level
        price_diff = (upper_price - lower_price) / (grid_levels - 1)
        if price_diff <= 0:
            logger.error(f"Price difference per level too small: {price_diff}")
            return False
        
        logger.info(f"Grid validation passed: {grid_levels} levels between {lower_price}-{upper_price}")
        return True
    
    def sanitize_input(self, value, input_type='string'):
        """
        Sanitize user input
        
        Args:
            value: Input value
            input_type (str): Type of input (string, float, int)
        
        Returns:
            Sanitized value or None if invalid
        """
        try:
            if input_type == 'string':
                if not isinstance(value, str):
                    return None
                # Remove potentially dangerous characters
                sanitized = re.sub(r'[^\w\-\.]', '', str(value))
                return sanitized.strip()
            
            elif input_type == 'float':
                return float(value)
            
            elif input_type == 'int':
                return int(value)
            
            else:
                return value
                
        except (ValueError, TypeError):
            logger.error(f"Failed to sanitize input: {value} as {input_type}")
            return None
