import streamlit as st
import asyncio
import threading
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime, timedelta
import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.binance_client import BinanceClient
from src.websocket_client import WebSocketClient
from src.technical_indicators import TechnicalIndicators
from src.data_processor import DataProcessor
from src.logger import setup_logger
from src.validation import Validator
from src.market_orders import MarketOrderHandler
from src.limit_orders import LimitOrderHandler
from src.advanced.oco import OCOOrderHandler
from src.advanced.twap import TWAPOrderHandler
from src.advanced.stop_limit import StopLimitOrderHandler
from src.advanced.grid_orders import GridOrderHandler

# Initialize logger
logger = setup_logger()

# Initialize session state
if 'binance_client' not in st.session_state:
    st.session_state.binance_client = None
if 'websocket_client' not in st.session_state:
    st.session_state.websocket_client = None
if 'data_processor' not in st.session_state:
    st.session_state.data_processor = DataProcessor()
if 'tech_indicators' not in st.session_state:
    st.session_state.tech_indicators = TechnicalIndicators()
if 'validator' not in st.session_state:
    st.session_state.validator = Validator()
if 'live_data' not in st.session_state:
    st.session_state.live_data = {}
if 'order_handlers' not in st.session_state:
    st.session_state.order_handlers = {}

def initialize_binance_client():
    """Initialize Binance client with API credentials"""
    try:
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_SECRET_KEY", "")
        
        if not api_key or not api_secret:
            st.error("Binance API credentials not found in environment variables")
            return False
            
        st.session_state.binance_client = BinanceClient(api_key, api_secret)
        
        # Initialize order handlers
        st.session_state.order_handlers = {
            'market': MarketOrderHandler(st.session_state.binance_client),
            'limit': LimitOrderHandler(st.session_state.binance_client),
            'oco': OCOOrderHandler(st.session_state.binance_client),
            'twap': TWAPOrderHandler(st.session_state.binance_client),
            'stop_limit': StopLimitOrderHandler(st.session_state.binance_client),
            'grid': GridOrderHandler(st.session_state.binance_client)
        }
        
        st.success("Binance client initialized successfully")
        logger.info("Binance client initialized")
        return True
    except Exception as e:
        st.error(f"Failed to initialize Binance client: {str(e)}")
        logger.error(f"Failed to initialize Binance client: {str(e)}")
        return False

def start_websocket():
    """Start WebSocket connection for live data"""
    try:
        if st.session_state.websocket_client is None:
            st.session_state.websocket_client = WebSocketClient()
        
        if not st.session_state.websocket_client.is_connected():
            st.session_state.websocket_client.connect()
            st.success("WebSocket connected")
            logger.info("WebSocket connection established")
    except Exception as e:
        st.error(f"Failed to start WebSocket: {str(e)}")
        logger.error(f"Failed to start WebSocket: {str(e)}")

def main():
    st.set_page_config(
        page_title="Binance Futures Trading Bot",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🚀 Binance Futures Trading Bot")
    st.markdown("### Real-time Trading with Advanced Technical Analysis")
    
    # Sidebar for API connection
    with st.sidebar:
        st.header("🔧 Connection Setup")
        
        if st.button("Initialize Binance Client"):
            initialize_binance_client()
        
        if st.button("Start WebSocket"):
            start_websocket()
        
        # Connection status
        if st.session_state.binance_client:
            st.success("✅ Binance Client Connected")
        else:
            st.error("❌ Binance Client Not Connected")
        
        if st.session_state.websocket_client and st.session_state.websocket_client.is_connected():
            st.success("✅ WebSocket Connected")
        else:
            st.error("❌ WebSocket Not Connected")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", 
        "📈 Trading", 
        "🔄 Advanced Orders", 
        "📉 Analysis", 
        "🧠 Sentiment", 
        "📋 Logs"
    ])
    
    with tab1:
        dashboard_page()
    
    with tab2:
        trading_page()
    
    with tab3:
        advanced_orders_page()
    
    with tab4:
        analysis_page()
    
    with tab5:
        sentiment_page()
    
    with tab6:
        logs_page()

def dashboard_page():
    """Main dashboard with live data and charts"""
    st.header("📊 Live Market Dashboard")
    
    # Symbol selection
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        symbol = st.selectbox("Select Symbol", ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"])
    
    with col2:
        timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"])
    
    with col3:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    if st.session_state.binance_client:
        try:
            # Get live market data
            ticker = st.session_state.binance_client.get_ticker(symbol)
            klines = st.session_state.binance_client.get_klines(symbol, timeframe, limit=100)
            
            if ticker and klines:
                # Display current price info
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Current Price", 
                        f"${float(ticker['lastPrice']):.4f}",
                        f"{float(ticker['priceChangePercent']):.2f}%"
                    )
                
                with col2:
                    st.metric("24h High", f"${float(ticker['highPrice']):.4f}")
                
                with col3:
                    st.metric("24h Low", f"${float(ticker['lowPrice']):.4f}")
                
                with col4:
                    st.metric("24h Volume", f"{float(ticker['volume']):.2f}")
                
                # Create candlestick chart with technical indicators
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                # Calculate technical indicators
                indicators = st.session_state.tech_indicators.calculate_all_indicators(df)
                
                # Create subplots
                fig = sp.make_subplots(
                    rows=3, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    subplot_titles=('Price & Indicators', 'RSI', 'MACD'),
                    row_heights=[0.6, 0.2, 0.2]
                )
                
                # Candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=df['timestamp'],
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        name=symbol
                    ),
                    row=1, col=1
                )
                
                # Add moving averages
                if 'sma_20' in indicators:
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=indicators['sma_20'],
                            name='SMA 20',
                            line=dict(color='orange')
                        ),
                        row=1, col=1
                    )
                
                if 'ema_20' in indicators:
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=indicators['ema_20'],
                            name='EMA 20',
                            line=dict(color='yellow')
                        ),
                        row=1, col=1
                    )
                
                # Bollinger Bands
                if all(key in indicators for key in ['bb_upper', 'bb_middle', 'bb_lower']):
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=indicators['bb_upper'],
                            name='BB Upper',
                            line=dict(color='gray', dash='dash')
                        ),
                        row=1, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=indicators['bb_lower'],
                            name='BB Lower',
                            line=dict(color='gray', dash='dash'),
                            fill='tonexty'
                        ),
                        row=1, col=1
                    )
                
                # RSI
                if 'rsi' in indicators:
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=indicators['rsi'],
                            name='RSI',
                            line=dict(color='purple')
                        ),
                        row=2, col=1
                    )
                    
                    # RSI overbought/oversold lines
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                
                # MACD
                if all(key in indicators for key in ['macd', 'macd_signal', 'macd_histogram']):
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=indicators['macd'],
                            name='MACD',
                            line=dict(color='blue')
                        ),
                        row=3, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=indicators['macd_signal'],
                            name='Signal',
                            line=dict(color='red')
                        ),
                        row=3, col=1
                    )
                    
                    fig.add_trace(
                        go.Bar(
                            x=df['timestamp'],
                            y=indicators['macd_histogram'],
                            name='Histogram',
                            marker_color='green'
                        ),
                        row=3, col=1
                    )
                
                fig.update_layout(height=800, showlegend=True, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Failed to load market data: {str(e)}")
            logger.error(f"Failed to load market data: {str(e)}")
    else:
        st.warning("Please initialize Binance client first")

def trading_page():
    """Basic trading page for market and limit orders"""
    st.header("📈 Basic Trading")
    
    if not st.session_state.binance_client:
        st.warning("Please initialize Binance client first")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Market Order")
        
        market_symbol = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT", "ADAUSDT"], key="market_symbol")
        market_side = st.selectbox("Side", ["BUY", "SELL"], key="market_side")
        market_quantity = st.number_input("Quantity", min_value=0.001, step=0.001, key="market_quantity")
        
        if st.button("Place Market Order"):
            if st.session_state.validator.validate_order(market_symbol, market_quantity, None):
                try:
                    result = st.session_state.order_handlers['market'].place_order(
                        market_symbol, market_side, market_quantity
                    )
                    if result:
                        st.success(f"Market order placed successfully: {result}")
                        logger.info(f"Market order placed: {result}")
                    else:
                        st.error("Failed to place market order")
                except Exception as e:
                    st.error(f"Error placing market order: {str(e)}")
                    logger.error(f"Error placing market order: {str(e)}")
            else:
                st.error("Invalid order parameters")
    
    with col2:
        st.subheader("📊 Limit Order")
        
        limit_symbol = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT", "ADAUSDT"], key="limit_symbol")
        limit_side = st.selectbox("Side", ["BUY", "SELL"], key="limit_side")
        limit_quantity = st.number_input("Quantity", min_value=0.001, step=0.001, key="limit_quantity")
        limit_price = st.number_input("Price", min_value=10000.0, value=118000.0, step=100.0, key="limit_price")
        
        if st.button("Place Limit Order"):
            if st.session_state.validator.validate_order(limit_symbol, limit_quantity, limit_price):
                try:
                    result = st.session_state.order_handlers['limit'].place_order(
                        limit_symbol, limit_side, limit_quantity, limit_price
                    )
                    if result:
                        st.success(f"Limit order placed successfully: {result}")
                        logger.info(f"Limit order placed: {result}")
                    else:
                        st.error("Failed to place limit order")
                except Exception as e:
                    st.error(f"Error placing limit order: {str(e)}")
                    logger.error(f"Error placing limit order: {str(e)}")
            else:
                st.error("Invalid order parameters")

def advanced_orders_page():
    """Advanced orders page"""
    st.header("🔄 Advanced Order Types")
    
    if not st.session_state.binance_client:
        st.warning("Please initialize Binance client first")
        return
    
    order_type = st.selectbox("Order Type", ["OCO", "TWAP", "Stop-Limit", "Grid Trading"])
    
    if order_type == "OCO":
        st.subheader("🎯 OCO (One-Cancels-Other) Order")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            oco_symbol = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT", "ADAUSDT"], key="oco_symbol")
            oco_side = st.selectbox("Side", ["BUY", "SELL"], key="oco_side")
            oco_quantity = st.number_input("Quantity", min_value=0.001, step=0.001, key="oco_quantity")
        
        with col2:
            oco_price = st.number_input("Limit Price", min_value=10000.0, value=118000.0, step=100.0, key="oco_price")
            oco_stop_price = st.number_input("Stop Price", min_value=10000.0, value=115000.0, step=100.0, key="oco_stop_price")
        
        with col3:
            oco_stop_limit_price = st.number_input("Stop Limit Price", min_value=10000.0, value=114000.0, step=100.0, key="oco_stop_limit_price")
        
        if st.button("Place OCO Order"):
            try:
                result = st.session_state.order_handlers['oco'].place_order(
                    oco_symbol, oco_side, oco_quantity, oco_price, oco_stop_price, oco_stop_limit_price
                )
                if result:
                    st.success(f"OCO order placed successfully: {result}")
                    logger.info(f"OCO order placed: {result}")
                else:
                    st.error("Failed to place OCO order")
            except Exception as e:
                st.error(f"Error placing OCO order: {str(e)}")
                logger.error(f"Error placing OCO order: {str(e)}")
    
    elif order_type == "TWAP":
        st.subheader("⏰ TWAP (Time-Weighted Average Price) Order")
        
        col1, col2 = st.columns(2)
        with col1:
            twap_symbol = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT", "ADAUSDT"], key="twap_symbol")
            twap_side = st.selectbox("Side", ["BUY", "SELL"], key="twap_side")
            twap_total_quantity = st.number_input("Total Quantity", min_value=0.001, step=0.001, key="twap_total_quantity")
        
        with col2:
            twap_duration_minutes = st.number_input("Duration (minutes)", min_value=1, step=1, key="twap_duration")
            twap_intervals = st.number_input("Number of Intervals", min_value=2, step=1, key="twap_intervals")
        
        if st.button("Start TWAP Order"):
            try:
                result = st.session_state.order_handlers['twap'].start_twap(
                    twap_symbol, twap_side, twap_total_quantity, twap_duration_minutes, twap_intervals
                )
                if result:
                    st.success(f"TWAP order started successfully: {result}")
                    logger.info(f"TWAP order started: {result}")
                else:
                    st.error("Failed to start TWAP order")
            except Exception as e:
                st.error(f"Error starting TWAP order: {str(e)}")
                logger.error(f"Error starting TWAP order: {str(e)}")
    
    elif order_type == "Stop-Limit":
        st.subheader("🛑 Stop-Limit Order")
        
        col1, col2 = st.columns(2)
        with col1:
            sl_symbol = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT", "ADAUSDT"], key="sl_symbol")
            sl_side = st.selectbox("Side", ["BUY", "SELL"], key="sl_side")
            sl_quantity = st.number_input("Quantity", min_value=0.001, step=0.001, key="sl_quantity")
        
        with col2:
            sl_stop_price = st.number_input("Stop Price", min_value=10000.0, value=115000.0, step=100.0, key="sl_stop_price")
            sl_limit_price = st.number_input("Limit Price", min_value=10000.0, value=118000.0, step=100.0, key="sl_limit_price")
        
        if st.button("Place Stop-Limit Order"):
            try:
                result = st.session_state.order_handlers['stop_limit'].place_order(
                    sl_symbol, sl_side, sl_quantity, sl_stop_price, sl_limit_price
                )
                if result:
                    st.success(f"Stop-limit order placed successfully: {result}")
                    logger.info(f"Stop-limit order placed: {result}")
                else:
                    st.error("Failed to place stop-limit order")
            except Exception as e:
                st.error(f"Error placing stop-limit order: {str(e)}")
                logger.error(f"Error placing stop-limit order: {str(e)}")
    
    elif order_type == "Grid Trading":
        st.subheader("📊 Grid Trading Strategy")
        
        col1, col2 = st.columns(2)
        with col1:
            grid_symbol = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT", "ADAUSDT"], key="grid_symbol")
            grid_upper_price = st.number_input("Upper Price", min_value=0.01, step=0.01, key="grid_upper_price")
            grid_lower_price = st.number_input("Lower Price", min_value=0.01, step=0.01, key="grid_lower_price")
        
        with col2:
            grid_levels = st.number_input("Grid Levels", min_value=3, max_value=20, step=1, key="grid_levels")
            grid_total_quantity = st.number_input("Total Quantity", min_value=0.001, step=0.001, key="grid_total_quantity")
        
        if st.button("Start Grid Trading"):
            try:
                result = st.session_state.order_handlers['grid'].start_grid(
                    grid_symbol, grid_upper_price, grid_lower_price, grid_levels, grid_total_quantity
                )
                if result:
                    st.success(f"Grid trading started successfully: {result}")
                    logger.info(f"Grid trading started: {result}")
                else:
                    st.error("Failed to start grid trading")
            except Exception as e:
                st.error(f"Error starting grid trading: {str(e)}")
                logger.error(f"Error starting grid trading: {str(e)}")

def analysis_page():
    """Historical data analysis page"""
    st.header("📉 Historical Data Analysis")
    
    # Load historical data
    try:
        historical_data = st.session_state.data_processor.load_historical_data()
        
        if historical_data is not None and not historical_data.empty:
            st.success(f"Loaded {len(historical_data)} historical trading records")
            
            # Basic statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_trades = len(historical_data)
                st.metric("Total Trades", f"{total_trades:,}")
            
            with col2:
                total_volume = historical_data['Size USD'].sum()
                st.metric("Total Volume", f"${total_volume:,.2f}")
            
            with col3:
                avg_trade_size = historical_data['Size USD'].mean()
                st.metric("Avg Trade Size", f"${avg_trade_size:.2f}")
            
            with col4:
                total_pnl = historical_data['Closed PnL'].sum()
                st.metric("Total PnL", f"${total_pnl:.2f}")
            
            # Trading patterns analysis
            st.subheader("📊 Trading Patterns")
            
            # Group by coin
            coin_analysis = historical_data.groupby('Coin').agg({
                'Size USD': ['count', 'sum', 'mean'],
                'Closed PnL': 'sum'
            }).round(2)
            
            st.dataframe(coin_analysis, use_container_width=True)
            
            # Time-based analysis using DateTime column created in data processor
            if 'DateTime' in historical_data.columns:
                daily_analysis = historical_data.groupby(historical_data['DateTime'].dt.date).agg({
                    'Size USD': 'sum',
                    'Closed PnL': 'sum'
                })
            else:
                # Fallback to creating DateTime from Timestamp
                historical_data['DateTime'] = pd.to_datetime(historical_data['Timestamp'].astype(float), unit='ms', errors='coerce')
                daily_analysis = historical_data.groupby(historical_data['DateTime'].dt.date).agg({
                    'Size USD': 'sum',
                    'Closed PnL': 'sum'
                })
            
            # Plot daily volume and PnL
            fig = sp.make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                subplot_titles=('Daily Trading Volume', 'Daily PnL')
            )
            
            fig.add_trace(
                go.Scatter(
                    x=daily_analysis.index,
                    y=daily_analysis['Size USD'],
                    name='Daily Volume',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=daily_analysis.index,
                    y=daily_analysis['Closed PnL'],
                    name='Daily PnL',
                    line=dict(color='green')
                ),
                row=2, col=1
            )
            
            fig.update_layout(height=600, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("No historical data available")
            
    except Exception as e:
        st.error(f"Failed to load historical data: {str(e)}")
        logger.error(f"Failed to load historical data: {str(e)}")

def sentiment_page():
    """Fear & Greed Index sentiment analysis page"""
    st.header("🧠 Market Sentiment Analysis")
    
    try:
        fear_greed_data = st.session_state.data_processor.load_fear_greed_data()
        
        if fear_greed_data is not None and not fear_greed_data.empty:
            st.success(f"Loaded {len(fear_greed_data)} Fear & Greed Index records")
            
            # Current sentiment (latest data)
            latest_record = fear_greed_data.iloc[-1]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Current Fear & Greed Index",
                    f"{latest_record['value']}",
                    latest_record['classification']
                )
            
            with col2:
                avg_30_days = fear_greed_data.tail(30)['value'].mean()
                st.metric("30-Day Average", f"{avg_30_days:.1f}")
            
            with col3:
                current_date = latest_record['date']
                if isinstance(current_date, pd.Timestamp):
                    current_date = current_date.strftime('%Y-%m-%d')
                st.metric("Last Updated", str(current_date))
            
            # Historical sentiment chart
            st.subheader("📈 Historical Fear & Greed Index")
            
            fig = go.Figure()
            
            # Color mapping for sentiment
            colors = {
                'Extreme Fear': 'red',
                'Fear': 'orange', 
                'Neutral': 'yellow',
                'Greed': 'lightgreen',
                'Extreme Greed': 'green'
            }
            
            for classification in colors.keys():
                subset = fear_greed_data[fear_greed_data['classification'] == classification]
                if not subset.empty:
                    fig.add_trace(go.Scatter(
                        x=pd.to_datetime(subset['date']),
                        y=subset['value'],
                        mode='markers',
                        name=classification,
                        marker=dict(color=colors[classification], size=4),
                        hovertemplate='<b>' + classification + '</b><br>Date: %{x}<br>Value: %{y}<extra></extra>'
                    ))
            
            # Add trend line
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(fear_greed_data['date']),
                y=fear_greed_data['value'],
                mode='lines',
                name='Trend',
                line=dict(color='black', width=1),
                opacity=0.5
            ))
            
            # Add sentiment zones
            fig.add_hrect(y0=0, y1=25, fillcolor="red", opacity=0.1, annotation_text="Extreme Fear")
            fig.add_hrect(y0=25, y1=45, fillcolor="orange", opacity=0.1, annotation_text="Fear")
            fig.add_hrect(y0=45, y1=55, fillcolor="yellow", opacity=0.1, annotation_text="Neutral")
            fig.add_hrect(y0=55, y1=75, fillcolor="lightgreen", opacity=0.1, annotation_text="Greed")
            fig.add_hrect(y0=75, y1=100, fillcolor="green", opacity=0.1, annotation_text="Extreme Greed")
            
            fig.update_layout(
                title="Fear & Greed Index Over Time",
                xaxis_title="Date",
                yaxis_title="Fear & Greed Index",
                height=600,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Sentiment statistics
            st.subheader("📊 Sentiment Statistics")
            
            sentiment_stats = fear_greed_data['classification'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart of sentiment distribution
                fig_pie = go.Figure(data=[go.Pie(
                    labels=sentiment_stats.index,
                    values=sentiment_stats.values,
                    marker_colors=[colors[label] for label in sentiment_stats.index]
                )])
                
                fig_pie.update_layout(title="Sentiment Distribution")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.dataframe(sentiment_stats, use_container_width=True)
                
        else:
            st.warning("No Fear & Greed Index data available")
            
    except Exception as e:
        st.error(f"Failed to load Fear & Greed Index data: {str(e)}")
        logger.error(f"Failed to load Fear & Greed Index data: {str(e)}")

def logs_page():
    """Trading logs display page"""
    st.header("📋 Trading Logs")
    
    try:
        if os.path.exists("bot.log"):
            with open("bot.log", "r") as f:
                logs = f.read()
            
            st.text_area("Bot Logs", logs, height=600)
            
            if st.button("🔄 Refresh Logs"):
                st.rerun()
                
            if st.button("🗑️ Clear Logs"):
                with open("bot.log", "w") as f:
                    f.write("")
                st.success("Logs cleared")
                st.rerun()
        else:
            st.info("No log file found. Logs will appear here once trading begins.")
            
    except Exception as e:
        st.error(f"Failed to load logs: {str(e)}")

if __name__ == "__main__":
    main()
