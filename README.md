# ZeroGamma Analysis Pipeline

Automated pipeline that fetches SPX zero gamma levels, analyzes market data with AI, and sends insights to Telegram.

## Features

- **SpotGamma Integration**: Fetches real-time SPX zero gamma levels via JWT-authenticated API
- **Market Data**: Retrieves 30-day OHLC data from Financial Modeling Prep
- **AI Analysis**: Uses OpenRouter's xiaomi/mimo-v2-flash model for market insights
- **Telegram Notifications**: Posts formatted analysis to group chats
- **Error Handling**: Comprehensive logging with graceful failure handling

## Pipeline Overview

```
SpotGamma API → Zero Gamma Level
                     ↓
FMP API → SPX OHLC (30-day) + Current Price
                     ↓
OpenRouter (xiaomi/mimo-v2-flash) → Market Analysis
                     ↓
Telegram Bot → Group Chat Message
                     ↓
zerogamma_analysis.log ← Error/Status logging
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example configuration:
```bash
cp .env.example .env
```

Edit `.env` with your API credentials:
```env
FMP_API_KEY=your_fmp_key
OPENROUTER_API_KEY=your_openrouter_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_group_chat_id
```

### 3. Run

```bash
python send_analysis.py
```

Optional: Analyze different symbol
```bash
python send_analysis.py --symbol QQQ
```

## Configuration

### API Keys

#### Financial Modeling Prep (FMP)
1. Visit https://financialmodelingprep.com/developer/docs
2. Sign up for free account
3. Copy your API key from dashboard

#### OpenRouter
1. Visit https://openrouter.ai/keys
2. Create account or sign in
3. Generate API key (free credits available)

#### Telegram Bot
1. Message [@BotFather](https://t.me/BotFather)
2. Use `/newbot` to create new bot
3. Save the bot token
4. Add bot to your group chat
5. Get group chat ID (typically negative number):
   ```bash
   python -c "from telegram import Bot; Bot('YOUR_BOT_TOKEN').get_updates()"
   ```

## Usage

### Manual Execution

```bash
python send_analysis.py
```

### Scheduled Execution

#### Linux/macOS (Cron)

Edit crontab:
```bash
crontab -e
```

Daily at 9:00 AM:
```cron
0 9 * * * cd /path/to/zerogamma && /usr/bin/python3 send_analysis.py >> zerogamma_analysis.log 2>&1
```

Every 4 hours:
```cron
0 */4 * * * cd /path/to/zerogamma && /usr/bin/python3 send_analysis.py >> zerogamma_analysis.log 2>&1
```

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 9:00 AM)
4. Set action:
   - Program: `C:\Python\python.exe`
   - Arguments: `C:\path\to\send_analysis.py`
   - Start in: `C:\path\to\zerogamma`
5. Set conditions: Run whether logged in or not
6. Run with highest privileges

## Output

The script produces:
- **Console logs**: Real-time execution status
- **zerogamma_analysis.log**: Detailed execution history
- **Telegram message**: Formatted analysis with:
  - Current SPX price
  - Zero gamma level
  - AI-powered market analysis

View logs:
```bash
tail -f zerogamma_analysis.log
```

## Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `send_analysis.py` | Main orchestration script |
| `config.py` | API key configuration loader |
| `fmp_data.py` | FMP historical OHLC data fetcher |
| `openrouter_analysis.py` | OpenRouter AI analysis integration |
| `telegram_sender.py` | Telegram messaging |

### Pipeline Steps

1. **Load Configuration** - Reads API keys from `.env`
2. **Fetch Zero Gamma** - Gets SPX zero gamma from SpotGamma API
3. **Fetch OHLC Data** - Retrieves 30-day SPX historical data from FMP
4. **Analyze** - Sends market data to OpenRouter for AI analysis
5. **Send Alert** - Posts results to Telegram group (non-critical failure)

## Error Handling

| Error | Behavior |
|-------|----------|
| **Missing API Keys** | Halts with clear error message |
| **FMP API Failure** | Logs error, halts pipeline |
| **OpenRouter Failure** | Logs error, halts pipeline |
| **Telegram Failure** | Logs warning, continues (non-critical) |

All errors logged to `zerogamma_analysis.log`

## Troubleshooting

### Missing environment variables
- Ensure `.env` exists in script directory
- Verify all required keys are set
- Check no typos in variable names

### FMP API error 429 (Rate Limited)
- Wait before retrying
- Consider upgrading FMP plan

### OpenRouter timeout
- Check internet connectivity
- Verify OpenRouter service status
- Retry after few minutes

### Telegram message not received
- Verify bot is added to group
- Check chat ID is correct (should be negative for groups)
- Review `zerogamma_analysis.log` for specific error

### Configuration error on startup
```
ValueError: Missing required environment variables: FMP_API_KEY, TELEGRAM_BOT_TOKEN
```
- Verify `.env` file exists and is in same directory as `send_analysis.py`
- Check all keys have values (not empty)

## Project Structure

```
zerogamma/
├── README.md                    # This file
├── SETUP.md                     # Detailed setup guide
├── requirements.txt             # Python dependencies
├── .env.example                 # Configuration template
├── send_analysis.py             # Main script
├── config.py                    # Configuration loader
├── fmp_data.py                  # FMP data fetcher
├── openrouter_analysis.py       # OpenRouter integration
├── telegram_sender.py           # Telegram sender
├── zerogamma_analysis.log       # Execution logs
└── reference/                   # Reference implementations
```

## Requirements

- Python 3.8+
- Active internet connection
- API keys for: FMP, OpenRouter, Telegram

## License

Part of Seasonal Vantage investment analysis suite.

## Support

For issues or questions, review logs in `zerogamma_analysis.log` or check troubleshooting section above.
