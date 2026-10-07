from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)
pd.set_option("display.float_format", lambda value: f"{value:,.4f}")
print("pandas", pd.__version__, "| yfinance", yf.__version__)

TICKERS = ["CVX", "XOM", "FANG"]
START_DATE = "2023-01-01"
END_DATE = "2024-12-31"
print("TICKERS:", TICKERS)
print("window:", START_DATE, "through the last trading day before", END_DATE)
print("These three firms are all U.S. oil and gas producers, but they are not the same business. "
      "CVX and XOM are integrated supermajors with refining and chemicals segments, while FANG is a "
      "smaller pure-play Permian shale producer. FANG's price should react more strongly to oil price "
      "swings, so keep that difference in mind when comparing returns and volatility.")