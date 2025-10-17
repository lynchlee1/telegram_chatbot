# DART Telegram Bot

A Python bot that automatically fetches corporate bond issuance data from DART (Data Analysis, Retrieval and Transfer system) and sends daily reports via Telegram.

## Features

1. **Get report data** from DART Open API
2. **Process** corporate bond issuance data (BW, CB, EB types)
3. **Send** formatted reports to Telegram using chatbot

## How it works

- Fetches daily corporate bond issuance reports from DART API
- Processes three types of bond data:
  - BW (Bond Warrant)
  - CB (Convertible Bond) 
  - EB (Exchangeable Bond)
- Formats data with company names, bond types, and amounts in Korean Won (억)
- Sends formatted reports to Telegram chat with timestamps in Korea time (UTC+9)
- Runs automatically via GitHub Actions on a scheduled basis

## Setup

### 1. DART API Key
- Register at [DART Open API](https://opendart.fss.or.kr/)
- Get your API key

### 2. Telegram Bot
- Create a bot via [@BotFather](https://t.me/botfather)
- Get bot token
- Get your chat ID

### 3. GitHub Secrets
Set these repository secrets:
- `DART_API_KEY`: Your DART API key
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token  
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID

### 4. GitHub Actions
- Workflow runs automatically on schedule
- Manual runs available via GitHub Actions tab

## Usage

The bot runs automatically and sends reports like:

```
2024-01-15 17:29 (월)
일일 누적 발행내역입니다.

- 삼성전자 BW 100.5억 
https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20240115000001

- LG화학 CB 250.0억
https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20240115000002
```

## Files

- `dart_bot.py` - Main bot script
- `requirements.txt` - Python dependencies
- `.github/workflows/` - GitHub Actions workflow (ignored in git)

## Dependencies

- `requests` - HTTP requests to DART API and Telegram
- `pandas` - Data processing (if needed)
- `Flask` - Web framework (if needed)

## License

MIT
