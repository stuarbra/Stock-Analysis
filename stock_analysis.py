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

raw = yf.download(
    TICKERS,
    start=START_DATE,
    end=END_DATE,
    auto_adjust=True,
    progress=False,
)
if raw is None or raw.empty:
    raise RuntimeError("No rows returned. Check the internet connection, tickers, and dates.")

# yfinance 1.x uses (Price, Ticker) column levels when group_by is not set.
long = raw.stack(level="Ticker", future_stack=True).rename_axis(["Date", "Ticker"]).reset_index()
long["Date"] = pd.to_datetime(long["Date"])
long = long.sort_values(["Ticker", "Date"]).reset_index(drop=True)

print("Loaded", len(long), "rows for", sorted(long["Ticker"].unique()))
print(long.head(3))

print("Shape (rows, columns):", long.shape)
print("\nData types:")
print(long.dtypes)
print("\nFirst five rows:")
print(long.head())
print("\nMissing values in each column:")
print(long.isna().sum().rename("missing_count").to_frame())
print("\nDate range:", long["Date"].min().date(), "to", long["Date"].max().date())
print("Number of records:", len(long))
Path("output").mkdir(exist_ok=True)
long.head().to_csv("output/first_five_rows.csv")
long.isna().sum().rename("missing_count").to_csv("output/missing_values.csv")