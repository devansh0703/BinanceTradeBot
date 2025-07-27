# Binance Futures Trading Bot

A comprehensive real-time trading bot for Binance USDT-M Futures with advanced order types, technical indicators, and market sentiment analysis. Built with Python and Streamlit for an intuitive web interface.

## 🚀 Features

### Real-Time Trading
- **Live Market Data**: Real-time price feeds and WebSocket streaming
- **Multiple Order Types**: Market, Limit, Stop-Limit, OCO, TWAP, and Grid trading
- **Technical Analysis**: 20+ indicators including RSI, MACD, Bollinger Bands, and moving averages
- **Risk Management**: Position tracking, portfolio management, and automated risk controls

### Advanced Analytics
- **Historical Data Analysis**: Analysis of 211,000+ historical trading records
- **Market Sentiment**: Fear & Greed Index integration with 2,600+ sentiment records
- **Pattern Recognition**: Automated trading pattern detection and analysis
- **Performance Metrics**: Comprehensive trading statistics and profitability analysis

### User Interface
- **Interactive Dashboard**: Streamlit-based web interface with real-time charts
- **Multi-Tab Navigation**: Organized interface for trading, analysis, and monitoring
- **Live Charts**: Candlestick charts with overlaid technical indicators
- **Responsive Design**: Mobile-friendly interface for trading on the go

## 📸 Screenshots

(screenshots/screenshot1.png)
(screenshots/screenshot2.png)
(screenshots/screenshot3.png)
(screenshots/screenshot4.png)
(screenshots/screenshot5.png)
(screenshots/screenshot6.png)

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Binance Futures API credentials
- Active internet connection for real-time data

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/devansh0703/BinanceTradeBot.git
   cd BinanceTradeBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API credentials**
   ```bash
   # Set environment variables
   export BINANCE_API_KEY="your_api_key_here"
   export BINANCE_SECRET_KEY="your_secret_key_here"
   ```

4. **Run the application**
   ```bash
   streamlit run app.py --server.port 5000
   ```

5. **Access the dashboard**
   Open your browser and navigate to `http://localhost:5000`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BINANCE_API_KEY` | Your Binance API key | Yes |
| `BINANCE_SECRET_KEY` | Your Binance secret key | Yes |

### API Setup

1. **Create Binance Account**
   - Sign up at [Binance](https://www.binance.com)
   - Complete identity verification

2. **Generate API Keys**
   - Go to API Management in your account settings
   - Create a new API key with Futures trading permissions
   - Enable IP restrictions for security

3. **Testnet (Recommended for Testing)**
   - Use [Binance Testnet](https://testnet.binancefuture.com) for safe testing
   - The bot automatically detects testnet credentials

## 📊 Order Types

### Basic Orders
- **Market Orders**: Immediate execution at current market price
- **Limit Orders**: Execute at specific price levels
- **Stop-Limit Orders**: Conditional orders triggered at stop price

### Advanced Orders
- **OCO (One-Cancels-Other)**: Simultaneous take-profit and stop-loss orders
- **TWAP (Time-Weighted Average Price)**: Split large orders over time
- **Grid Trading**: Automated buy-low/sell-high within price ranges

## 📈 Technical Indicators

### Trend Indicators
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Weighted Moving Average (WMA)
- MACD (Moving Average Convergence Divergence)

### Momentum Indicators
- RSI (Relative Strength Index)
- Stochastic Oscillator
- Williams %R
- Rate of Change (ROC)

### Volatility Indicators
- Bollinger Bands
- Average True Range (ATR)
- Keltner Channels
- Standard Deviation

### Volume Indicators
- On-Balance Volume (OBV)
- Volume Weighted Average Price (VWAP)
- Accumulation/Distribution Line
- Money Flow Index (MFI)

## 📁 Project Structure

```
BinanceTradeBot/
├── app.py                      # Main Streamlit application
├── src/                        # Source code modules
│   ├── binance_client.py       # Binance API client
│   ├── websocket_client.py     # WebSocket streaming client
│   ├── technical_indicators.py # Technical analysis engine
│   ├── data_processor.py       # Historical data processor
│   ├── validator.py            # Input validation
│   ├── logger.py              # Logging system
│   └── advanced/              # Advanced order handlers
│       ├── market.py          # Market orders
│       ├── limit.py           # Limit orders
│       ├── stop_limit.py      # Stop-limit orders
│       ├── oco.py             # OCO orders
│       ├── twap.py            # TWAP orders
│       └── grid_orders.py     # Grid trading
├── attached_assets/           # Historical data files
│   ├── historical_data_*.csv  # 211K+ trading records
│   └── fear_greed_index_*.csv # 2.6K+ sentiment records
├── screenshots/               # Application screenshots
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

## 🔍 Data Analysis

### Historical Trading Data
- **211,000+ Records**: Comprehensive trading history analysis
- **Multi-Asset Coverage**: BTC, ETH, ADA, SOL, DOT, and more
- **Performance Metrics**: Win rate, profit/loss ratios, trade sizing
- **Pattern Recognition**: Automated detection of profitable patterns

### Market Sentiment Analysis
- **Fear & Greed Index**: 2,600+ historical sentiment records
- **Market Psychology**: Correlation between sentiment and price movements
- **Trend Analysis**: Long-term sentiment trends and market cycles
- **Predictive Insights**: Sentiment-based trading signals

## ⚠️ Risk Management

### Built-in Safety Features
- **Testnet Integration**: Safe testing environment
- **Position Limits**: Configurable maximum position sizes
- **Stop-Loss Protection**: Automatic loss limitation
- **Input Validation**: Comprehensive parameter checking

### Best Practices
1. **Start with Testnet**: Always test strategies before live trading
2. **Risk Per Trade**: Never risk more than 1-2% per trade
3. **Diversification**: Spread risk across multiple assets
4. **Regular Monitoring**: Keep track of open positions
5. **Stop-Loss Orders**: Always use protective stops

## 🚨 Troubleshooting

### Common Issues

#### API Connection Errors
```
Error: API request failed
Solution: Check API credentials and internet connection
```

#### WebSocket Connection Issues
```
Error: WebSocket connection timeout
Solution: Verify network connectivity and firewall settings
```

#### Order Placement Failures
```
Error: Price less than min price
Solution: Check minimum price increments for the symbol
```

#### Data Loading Errors
```
Error: Failed to load historical data
Solution: Ensure CSV files are in attached_assets/ directory
```

### Debug Mode
Enable detailed logging by setting the log level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 API Documentation

### Binance Futures API
- [Official Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- [WebSocket Streams](https://binance-docs.github.io/apidocs/futures/en/#websocket-market-streams)
- [Error Codes](https://binance-docs.github.io/apidocs/futures/en/#error-codes)

### Rate Limits
- **Request Weight**: 1200 per minute
- **Orders**: 300 per 10 seconds
- **Raw Requests**: 6000 per 5 minutes

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Include error handling

### Testing
```bash
# Run tests
python -m pytest tests/

# Check code coverage
python -m pytest --cov=src tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚖️ Disclaimer

**Important Notice**: This software is for educational and research purposes only. Trading cryptocurrencies involves substantial risk of loss and is not suitable for all investors. The authors and contributors are not responsible for any financial losses incurred through the use of this software.

### Risk Factors
- **High Volatility**: Cryptocurrency markets are extremely volatile
- **Technical Risk**: Software bugs may cause unexpected behavior
- **Market Risk**: Past performance does not guarantee future results
- **Regulatory Risk**: Cryptocurrency regulations may change

### Recommendations
- Only trade with funds you can afford to lose
- Thoroughly test all strategies in testnet environment
- Understand the risks before live trading
- Consider consulting with a financial advisor

## 🆘 Support

### Getting Help
- **Issues**: Report bugs on [GitHub Issues](https://github.com/devansh0703/BinanceTradeBot/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/devansh0703/BinanceTradeBot/discussions)
- **Documentation**: Check this README and code comments

### Contact
- **GitHub**: [@devansh0703](https://github.com/devansh0703)
- **Repository**: [BinanceTradeBot](https://github.com/devansh0703/BinanceTradeBot)

## 🙏 Acknowledgments

- **Binance**: For providing comprehensive API documentation
- **Streamlit**: For the excellent web framework
- **Plotly**: For interactive charting capabilities
- **Python Community**: For the amazing ecosystem of libraries

---

**Built with ❤️ for the trading community**

*Last updated: July 2025*
