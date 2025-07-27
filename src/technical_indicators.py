"""
Technical indicators calculation module
"""

import pandas as pd
import numpy as np
from .logger import setup_logger

logger = setup_logger()

class TechnicalIndicators:
    def __init__(self):
        """Initialize technical indicators calculator"""
        logger.info("Technical indicators calculator initialized")
    
    def sma(self, data, period):
        """
        Simple Moving Average
        
        Args:
            data (pd.Series): Price data
            period (int): Period for SMA
        
        Returns:
            pd.Series: SMA values
        """
        return data.rolling(window=period).mean()
    
    def ema(self, data, period):
        """
        Exponential Moving Average
        
        Args:
            data (pd.Series): Price data
            period (int): Period for EMA
        
        Returns:
            pd.Series: EMA values
        """
        return data.ewm(span=period, adjust=False).mean()
    
    def rsi(self, data, period=14):
        """
        Relative Strength Index
        
        Args:
            data (pd.Series): Price data
            period (int): Period for RSI calculation
        
        Returns:
            pd.Series: RSI values
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def macd(self, data, fast_period=12, slow_period=26, signal_period=9):
        """
        Moving Average Convergence Divergence
        
        Args:
            data (pd.Series): Price data
            fast_period (int): Fast EMA period
            slow_period (int): Slow EMA period
            signal_period (int): Signal line EMA period
        
        Returns:
            tuple: (MACD line, Signal line, Histogram)
        """
        ema_fast = self.ema(data, fast_period)
        ema_slow = self.ema(data, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def bollinger_bands(self, data, period=20, std_dev=2):
        """
        Bollinger Bands
        
        Args:
            data (pd.Series): Price data
            period (int): Period for moving average
            std_dev (float): Standard deviation multiplier
        
        Returns:
            tuple: (Upper band, Middle band, Lower band)
        """
        middle_band = self.sma(data, period)
        std = data.rolling(window=period).std()
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    def stochastic(self, high, low, close, k_period=14, d_period=3):
        """
        Stochastic Oscillator
        
        Args:
            high (pd.Series): High prices
            low (pd.Series): Low prices
            close (pd.Series): Close prices
            k_period (int): %K period
            d_period (int): %D period
        
        Returns:
            tuple: (%K, %D)
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent, d_percent
    
    def williams_r(self, high, low, close, period=14):
        """
        Williams %R
        
        Args:
            high (pd.Series): High prices
            low (pd.Series): Low prices
            close (pd.Series): Close prices
            period (int): Period for calculation
        
        Returns:
            pd.Series: Williams %R values
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
        
        return wr
    
    def atr(self, high, low, close, period=14):
        """
        Average True Range
        
        Args:
            high (pd.Series): High prices
            low (pd.Series): Low prices
            close (pd.Series): Close prices
            period (int): Period for ATR
        
        Returns:
            pd.Series: ATR values
        """
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def adx(self, high, low, close, period=14):
        """
        Average Directional Index
        
        Args:
            high (pd.Series): High prices
            low (pd.Series): Low prices
            close (pd.Series): Close prices
            period (int): Period for ADX
        
        Returns:
            tuple: (ADX, +DI, -DI)
        """
        high_diff = high.diff()
        low_diff = low.diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = (-low_diff).where((low_diff > high_diff) & (low_diff > 0), 0)
        
        tr = self.atr(high, low, close, 1)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    def calculate_all_indicators(self, df):
        """
        Calculate all technical indicators for a DataFrame
        
        Args:
            df (pd.DataFrame): OHLCV data
        
        Returns:
            dict: Dictionary containing all calculated indicators
        """
        try:
            indicators = {}
            
            # Ensure we have the required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.error("DataFrame missing required OHLCV columns")
                return {}
            
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']
            
            # Moving Averages
            indicators['sma_10'] = self.sma(close, 10)
            indicators['sma_20'] = self.sma(close, 20)
            indicators['sma_50'] = self.sma(close, 50)
            indicators['ema_10'] = self.ema(close, 10)
            indicators['ema_20'] = self.ema(close, 20)
            indicators['ema_50'] = self.ema(close, 50)
            
            # RSI
            indicators['rsi'] = self.rsi(close)
            
            # MACD
            macd_line, signal_line, histogram = self.macd(close)
            indicators['macd'] = macd_line
            indicators['macd_signal'] = signal_line
            indicators['macd_histogram'] = histogram
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.bollinger_bands(close)
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            
            # Stochastic
            k_percent, d_percent = self.stochastic(high, low, close)
            indicators['stoch_k'] = k_percent
            indicators['stoch_d'] = d_percent
            
            # Williams %R
            indicators['williams_r'] = self.williams_r(high, low, close)
            
            # ATR
            indicators['atr'] = self.atr(high, low, close)
            
            # ADX
            adx, plus_di, minus_di = self.adx(high, low, close)
            indicators['adx'] = adx
            indicators['plus_di'] = plus_di
            indicators['minus_di'] = minus_di
            
            # Volume indicators
            indicators['volume_sma'] = self.sma(volume, 20)
            
            logger.info("All technical indicators calculated successfully")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return {}
    
    def generate_signals(self, indicators, current_price):
        """
        Generate trading signals based on technical indicators
        
        Args:
            indicators (dict): Dictionary of calculated indicators
            current_price (float): Current market price
        
        Returns:
            dict: Dictionary containing trading signals
        """
        try:
            signals = {
                'overall': 'NEUTRAL',
                'strength': 0,
                'details': []
            }
            
            signal_score = 0
            signal_count = 0
            
            # RSI signals
            if 'rsi' in indicators and not indicators['rsi'].empty:
                rsi_current = indicators['rsi'].iloc[-1]
                if not pd.isna(rsi_current):
                    if rsi_current < 30:
                        signals['details'].append("RSI oversold - BUY signal")
                        signal_score += 2
                    elif rsi_current > 70:
                        signals['details'].append("RSI overbought - SELL signal")
                        signal_score -= 2
                    elif rsi_current < 50:
                        signal_score += 1
                    else:
                        signal_score -= 1
                    signal_count += 1
            
            # MACD signals
            if all(key in indicators for key in ['macd', 'macd_signal']):
                macd_current = indicators['macd'].iloc[-1]
                signal_current = indicators['macd_signal'].iloc[-1]
                
                if not pd.isna(macd_current) and not pd.isna(signal_current):
                    if macd_current > signal_current:
                        signals['details'].append("MACD bullish crossover")
                        signal_score += 1
                    else:
                        signals['details'].append("MACD bearish crossover")
                        signal_score -= 1
                    signal_count += 1
            
            # Bollinger Bands signals
            if all(key in indicators for key in ['bb_upper', 'bb_lower']):
                bb_upper = indicators['bb_upper'].iloc[-1]
                bb_lower = indicators['bb_lower'].iloc[-1]
                
                if not pd.isna(bb_upper) and not pd.isna(bb_lower):
                    if current_price <= bb_lower:
                        signals['details'].append("Price at lower Bollinger Band - BUY signal")
                        signal_score += 2
                    elif current_price >= bb_upper:
                        signals['details'].append("Price at upper Bollinger Band - SELL signal")
                        signal_score -= 2
                    signal_count += 1
            
            # Moving Average signals
            if 'ema_20' in indicators and 'sma_20' in indicators:
                ema_current = indicators['ema_20'].iloc[-1]
                sma_current = indicators['sma_20'].iloc[-1]
                
                if not pd.isna(ema_current) and not pd.isna(sma_current):
                    if current_price > ema_current and current_price > sma_current:
                        signals['details'].append("Price above moving averages - Bullish")
                        signal_score += 1
                    elif current_price < ema_current and current_price < sma_current:
                        signals['details'].append("Price below moving averages - Bearish")
                        signal_score -= 1
                    signal_count += 1
            
            # Calculate overall signal
            if signal_count > 0:
                signals['strength'] = signal_score / signal_count
                
                if signals['strength'] > 1:
                    signals['overall'] = 'STRONG_BUY'
                elif signals['strength'] > 0.5:
                    signals['overall'] = 'BUY'
                elif signals['strength'] > -0.5:
                    signals['overall'] = 'NEUTRAL'
                elif signals['strength'] > -1:
                    signals['overall'] = 'SELL'
                else:
                    signals['overall'] = 'STRONG_SELL'
            
            logger.info(f"Trading signals generated: {signals['overall']} (strength: {signals['strength']:.2f})")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {str(e)}")
            return {'overall': 'NEUTRAL', 'strength': 0, 'details': ['Error generating signals']}
