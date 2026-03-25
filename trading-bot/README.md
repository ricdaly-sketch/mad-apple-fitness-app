# Polymarket Arbitrage Trading Bot

Scans Polymarket prediction markets every few seconds for pricing inefficiencies and executes trades when the market price diverges from the estimated fair probability.

## Strategy

1. Fetch all active Polymarket markets
2. Estimate fair probability for each outcome using an external model or heuristic
3. If `market_price < fair_prob - min_edge`, **BUY** (market is underpricing the outcome)
4. Once price corrects, **HEDGE/SELL** to lock in profit
5. Track P&L in real time

## Setup

```bash
cd trading-bot
pip install -r requirements.txt
cp .env.example .env
# Fill in your credentials in .env
```

## Run

```bash
# Paper trading (no real money)
python bot.py --paper

# Live trading
python bot.py --live
```

## Configuration

Edit `config.py` to adjust:
- `MIN_EDGE` – minimum price/probability gap to trigger a trade (default 0.03)
- `MAX_LATENCY_MS` – max acceptable data staleness in ms (default 30)
- `SCAN_INTERVAL_S` – seconds between market scans (default 5)
- `MAX_POSITION_USDC` – max size per trade in USDC

## Disclaimer

This is for educational purposes. Trading prediction markets carries financial risk. Always test with paper trading first.
