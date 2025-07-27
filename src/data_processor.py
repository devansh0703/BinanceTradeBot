"""
Data processor for historical trading data and Fear & Greed Index
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from .logger import setup_logger

logger = setup_logger()

class DataProcessor:
    def __init__(self):
        """Initialize data processor"""
        self.historical_data = None
        self.fear_greed_data = None
        logger.info("Data processor initialized")
    
    def load_historical_data(self, file_path="attached_assets/historical_data_1753604303963.csv"):
        """
        Load historical trading data from CSV
        
        Args:
            file_path (str): Path to historical data CSV file
        
        Returns:
            pd.DataFrame: Historical trading data
        """
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                
                # Clean and process the data
                df['Timestamp'] = pd.to_numeric(df['Timestamp'], errors='coerce')
                df['Size USD'] = pd.to_numeric(df['Size USD'], errors='coerce')
                df['Execution Price'] = pd.to_numeric(df['Execution Price'], errors='coerce')
                df['Size Tokens'] = pd.to_numeric(df['Size Tokens'], errors='coerce')
                df['Closed PnL'] = pd.to_numeric(df['Closed PnL'], errors='coerce')
                
                # Remove rows with invalid data
                df = df.dropna(subset=['Timestamp', 'Size USD', 'Execution Price'])
                
                # Convert timestamp to datetime - handle different timestamp formats
                if not df.empty and not df['Timestamp'].isna().all():
                    # Convert scientific notation and determine units
                    df['Timestamp'] = df['Timestamp'].astype(float)
                    sample_timestamp = df['Timestamp'].iloc[0]
                    
                    if sample_timestamp > 1e15:  # Nanoseconds (like 1.73E+18)
                        df['DateTime'] = pd.to_datetime(df['Timestamp'], unit='ns', errors='coerce')
                    elif sample_timestamp > 1e12:  # Milliseconds (like 1.73E+12)
                        df['DateTime'] = pd.to_datetime(df['Timestamp'], unit='ms', errors='coerce')
                    elif sample_timestamp > 1e9:   # Seconds (like 1.73E+09)
                        df['DateTime'] = pd.to_datetime(df['Timestamp'], unit='s', errors='coerce')
                    else:
                        # Fallback - try different units
                        try:
                            df['DateTime'] = pd.to_datetime(df['Timestamp'], unit='ms', errors='coerce')
                        except:
                            df['DateTime'] = pd.to_datetime(df['Timestamp'], unit='s', errors='coerce')
                
                self.historical_data = df
                logger.info(f"Loaded {len(df)} historical trading records")
                return df
            else:
                logger.error(f"Historical data file not found: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            return None
    
    def load_fear_greed_data(self, file_path="attached_assets/fear_greed_index_1753604296223.csv"):
        """
        Load Fear & Greed Index data from CSV
        
        Args:
            file_path (str): Path to Fear & Greed Index CSV file
        
        Returns:
            pd.DataFrame: Fear & Greed Index data
        """
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                
                # Clean and process the data
                df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df['date'] = pd.to_datetime(df['date'])
                
                # Remove rows with invalid data
                df = df.dropna(subset=['timestamp', 'value', 'date'])
                
                # Sort by date
                df = df.sort_values('date')
                
                self.fear_greed_data = df
                logger.info(f"Loaded {len(df)} Fear & Greed Index records")
                return df
            else:
                logger.error(f"Fear & Greed Index file not found: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading Fear & Greed Index data: {str(e)}")
            return None
    
    def analyze_trading_patterns(self):
        """
        Analyze trading patterns from historical data
        
        Returns:
            dict: Analysis results
        """
        try:
            if self.historical_data is None:
                self.load_historical_data()
            
            if self.historical_data is None or self.historical_data.empty:
                return {}
            
            analysis = {}
            
            # Basic statistics
            analysis['total_trades'] = len(self.historical_data)
            analysis['total_volume_usd'] = self.historical_data['Size USD'].sum()
            analysis['avg_trade_size'] = self.historical_data['Size USD'].mean()
            analysis['total_pnl'] = self.historical_data['Closed PnL'].sum()
            
            # Performance by coin
            coin_analysis = self.historical_data.groupby('Coin').agg({
                'Size USD': ['count', 'sum', 'mean'],
                'Closed PnL': 'sum',
                'Execution Price': ['min', 'max', 'mean']
            }).round(2)
            analysis['coin_performance'] = coin_analysis
            
            # Time-based analysis
            self.historical_data['Date'] = self.historical_data['DateTime'].dt.date
            daily_stats = self.historical_data.groupby('Date').agg({
                'Size USD': 'sum',
                'Closed PnL': 'sum',
                'Account': 'count'
            })
            analysis['daily_performance'] = daily_stats
            
            # Side analysis (BUY vs SELL)
            side_analysis = self.historical_data.groupby('Side').agg({
                'Size USD': ['count', 'sum', 'mean'],
                'Closed PnL': 'sum'
            }).round(2)
            analysis['side_performance'] = side_analysis
            
            # Profit/Loss analysis
            profitable_trades = self.historical_data[self.historical_data['Closed PnL'] > 0]
            losing_trades = self.historical_data[self.historical_data['Closed PnL'] < 0]
            
            analysis['profitability'] = {
                'profitable_trades': len(profitable_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(profitable_trades) / len(self.historical_data) * 100,
                'avg_profit': profitable_trades['Closed PnL'].mean() if not profitable_trades.empty else 0,
                'avg_loss': losing_trades['Closed PnL'].mean() if not losing_trades.empty else 0
            }
            
            logger.info("Trading pattern analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing trading patterns: {str(e)}")
            return {}
    
    def analyze_sentiment_correlation(self):
        """
        Analyze correlation between Fear & Greed Index and market performance
        
        Returns:
            dict: Sentiment correlation analysis
        """
        try:
            if self.fear_greed_data is None:
                self.load_fear_greed_data()
            
            if self.fear_greed_data is None or self.fear_greed_data.empty:
                return {}
            
            analysis = {}
            
            # Current sentiment
            latest_sentiment = self.fear_greed_data.iloc[-1]
            analysis['current_sentiment'] = {
                'value': latest_sentiment['value'],
                'classification': latest_sentiment['classification'],
                'date': latest_sentiment['date'].strftime('%Y-%m-%d')
            }
            
            # Historical sentiment distribution
            sentiment_dist = self.fear_greed_data['classification'].value_counts()
            analysis['sentiment_distribution'] = sentiment_dist.to_dict()
            
            # Sentiment statistics
            analysis['sentiment_stats'] = {
                'avg_value': self.fear_greed_data['value'].mean(),
                'min_value': self.fear_greed_data['value'].min(),
                'max_value': self.fear_greed_data['value'].max(),
                'std_value': self.fear_greed_data['value'].std()
            }
            
            # Recent sentiment trends
            last_30_days = self.fear_greed_data.tail(30)
            last_7_days = self.fear_greed_data.tail(7)
            
            analysis['recent_trends'] = {
                'avg_30_days': last_30_days['value'].mean(),
                'avg_7_days': last_7_days['value'].mean(),
                'trend_30_days': 'Improving' if last_7_days['value'].mean() > last_30_days['value'].mean() else 'Declining'
            }
            
            # Extreme sentiment periods
            extreme_fear = self.fear_greed_data[self.fear_greed_data['classification'] == 'Extreme Fear']
            extreme_greed = self.fear_greed_data[self.fear_greed_data['classification'] == 'Extreme Greed']
            
            analysis['extreme_periods'] = {
                'extreme_fear_days': len(extreme_fear),
                'extreme_greed_days': len(extreme_greed),
                'extreme_fear_avg': extreme_fear['value'].mean() if not extreme_fear.empty else 0,
                'extreme_greed_avg': extreme_greed['value'].mean() if not extreme_greed.empty else 0
            }
            
            logger.info("Sentiment correlation analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment correlation: {str(e)}")
            return {}
    
    def get_sentiment_signal(self, current_value=None):
        """
        Get trading signal based on Fear & Greed Index
        
        Args:
            current_value (float, optional): Current Fear & Greed value
        
        Returns:
            dict: Sentiment-based trading signal
        """
        try:
            if current_value is None:
                if self.fear_greed_data is None:
                    self.load_fear_greed_data()
                
                if self.fear_greed_data is None or self.fear_greed_data.empty:
                    return {'signal': 'NEUTRAL', 'confidence': 0, 'reason': 'No sentiment data'}
                
                current_value = self.fear_greed_data.iloc[-1]['value']
            
            signal = {}
            
            if current_value <= 20:
                signal = {
                    'signal': 'STRONG_BUY',
                    'confidence': 0.8,
                    'reason': 'Extreme Fear - Potential buying opportunity'
                }
            elif current_value <= 40:
                signal = {
                    'signal': 'BUY',
                    'confidence': 0.6,
                    'reason': 'Fear sentiment - Consider buying'
                }
            elif current_value <= 60:
                signal = {
                    'signal': 'NEUTRAL',
                    'confidence': 0.3,
                    'reason': 'Neutral sentiment'
                }
            elif current_value <= 80:
                signal = {
                    'signal': 'SELL',
                    'confidence': 0.6,
                    'reason': 'Greed sentiment - Consider taking profits'
                }
            else:
                signal = {
                    'signal': 'STRONG_SELL',
                    'confidence': 0.8,
                    'reason': 'Extreme Greed - High risk of correction'
                }
            
            logger.info(f"Sentiment signal generated: {signal['signal']} (confidence: {signal['confidence']})")
            return signal
            
        except Exception as e:
            logger.error(f"Error generating sentiment signal: {str(e)}")
            return {'signal': 'NEUTRAL', 'confidence': 0, 'reason': 'Error generating signal'}
    
    def calculate_volatility_metrics(self, symbol='BTCUSDT', timeframe='1h'):
        """
        Calculate historical volatility metrics
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe for analysis
        
        Returns:
            dict: Volatility metrics
        """
        try:
            # This would typically use the historical_data to calculate volatility
            # For now, we'll provide a basic implementation
            
            if self.historical_data is None:
                self.load_historical_data()
            
            if self.historical_data is None or self.historical_data.empty:
                return {}
            
            # Filter data for the specific symbol if available
            symbol_data = self.historical_data
            
            if 'Execution Price' not in symbol_data.columns:
                return {}
            
            prices = symbol_data['Execution Price'].dropna()
            
            if len(prices) < 2:
                return {}
            
            # Calculate returns
            returns = prices.pct_change().dropna()
            
            metrics = {
                'daily_volatility': returns.std(),
                'annualized_volatility': returns.std() * np.sqrt(365),
                'max_drawdown': (prices / prices.expanding().max() - 1).min(),
                'sharpe_ratio': returns.mean() / returns.std() if returns.std() != 0 else 0,
                'var_95': np.percentile(returns, 5),
                'var_99': np.percentile(returns, 1)
            }
            
            logger.info(f"Volatility metrics calculated for {symbol}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating volatility metrics: {str(e)}")
            return {}
