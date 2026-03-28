# Bot configuration

MIN_EDGE = 0.01          # Minimum price/probability gap to open a trade
MAX_LATENCY_MS = 500     # Max acceptable staleness of market data (ms)
SCAN_INTERVAL_S = 5      # Seconds between full market scans
MAX_POSITION_USDC = 50   # Max size per trade in USDC
MIN_LIQUIDITY_USDC = 100 # Minimum market liquidity to consider
TAKE_PROFIT_EDGE = 0.005 # Close position when edge drops below this

# Polymarket CLOB API base URL
CLOB_BASE_URL = "https://clob.polymarket.com"

# Markets to scan (empty list = scan all active markets)
WATCHLIST: list[str] = []
