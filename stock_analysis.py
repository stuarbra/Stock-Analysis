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

# Calculate daily returns
long["Daily_Return"] = long.groupby("Ticker")["Close"].pct_change()

print("\nDaily returns calculated. First five rows with daily returns:")
print(
    long.groupby("Ticker")
    .head()
    [["Date", "Ticker", "Close", "Daily_Return"]]
)

# Descriptive statistics for daily returns and closing prices
stats = long.groupby("Ticker")[["Close", "Daily_Return"]].agg(
    ["count", "mean", "median", "min", "max", "std"]
)

print("\nDescriptive statistics by stock:")
print(stats)

# Save descriptive statistics to a CSV file
stats.to_csv("output/descriptive_statistics.csv")

# Correlation matrix of daily returns
correlation_matrix = long.pivot(index="Date", columns="Ticker", values="Daily_Return").corr()

print("\nCorrelation matrix of daily returns:")
print(correlation_matrix)

# Save correlation matrix to a CSV file
correlation_matrix.to_csv("output/correlation_matrix.csv")

# Load the interpretation
print("\nCorrelation Interpretation:")
print(
    "All three stocks have positive correlations in their daily returns, "
    "suggesting that they tend to move together rather than independently. "
    "CVX and XOM have the strongest correlation (0.7907), while CVX and FANG "
    "have the weakest correlation (0.6663)."
)

# Monthly average closing prices by ticker
monthly_summary = (
    long.groupby(["Ticker", pd.Grouper(key="Date", freq="MS")])["Close"]
    .mean()
    .reset_index()
)

monthly_summary["Close"] = monthly_summary["Close"].round(2)

print("\nMonthly Average Closing Price by Stock:")
print(
    monthly_summary.pivot(
        index="Date",
        columns="Ticker",
        values="Close"
    ).to_string()
)

# Save the monthly summary
monthly_summary.to_csv("output/monthly_average_closing_price.csv", index=False)

print("\nBusiness Story")

# Finds the biggest positive and negative movement for each stock

movement_rows = []
for ticker, ticker_prices in long.groupby('Ticker'):
    valid_returns = ticker_prices.dropna(subset=['Daily_Return']).copy()

    biggest_gain = valid_returns.loc[valid_returns['Daily_Return'].idxmax()]
    biggest_loss = valid_returns.loc[valid_returns['Daily_Return'].idxmin()]

    movement_rows.append({
        'Ticker': ticker,
        'Type': 'Biggest Gain',
        'Event_Date': biggest_gain['Date'],
        'Daily_Return': biggest_gain['Daily_Return'],
        'Close': biggest_gain['Close'],
        'Volume': biggest_gain['Volume'],
    })
    movement_rows.append({
        'Ticker': ticker,
        'Type': 'Biggest Loss', 
        'Event_Date': biggest_loss['Date'],
        'Daily_Return': biggest_loss['Daily_Return'],
        'Close': biggest_loss['Close'],
        'Volume': biggest_loss['Volume'],
    })
movement_candidates = pd.DataFrame(movement_rows).sort_values(['Ticker', 'Type'])
print("\nLargest one-day gain and loss for each ticker")
print(movement_candidates.to_string(index=False))

#Additional OHLCV & Daily Returns for each stock 

for ticker, ticker_data in long.groupby("Ticker"):
    biggest_gain = ticker_data.sort_values(
        "Daily_Return", ascending=False
    ).iloc[0]
    biggest_loss = ticker_data.sort_values(
        "Daily_Return", ascending=True
    ).iloc[0]

    print("\n" + ticker)
    print("\nBiggest gain:", biggest_gain)
    print("\nBiggest loss:", biggest_loss)

print("\nBusiness Story Summary:"
"\nMovement Chosen for each stock:"
"\nCVX - OCTOBER 27TH, 2023"
"\nNegative movement - Total earning dropped"
"\nFANG - FEBRUARY 13TH, 2024 "
"\nPositive movement - Merger with Endeavor Energy"
"\nXOM - APRIL 3RD, 2023 "
"\nPositive movement - OPEC+ meeting and production cuts announcement"
)

#Visualization 
# Chart 1 : Normalized price performance across the analysis period
Path("charts").mkdir(exist_ok=True)
price_matrix = long.pivot(index="Date", columns="Ticker", values="Close")
normalized = (
    price_matrix
    .div(price_matrix.iloc[0])
    .mul(100)
)

normalized.plot(figsize=(10, 6))
plt.title("Normalized price performance across the analysis period")
plt.xlabel("Date")
plt.ylabel("Indexed price (first observation = 100)")
plt.tight_layout()
plt.savefig("charts/normalized_prices.png", dpi=150)
plt.show()

#Chart 2 : Significant movement period for CVX
Path("charts").mkdir(exist_ok=True)

event_choice = movement_candidates[
    (movement_candidates['Ticker'] == 'CVX') 
    & (movement_candidates['Type'] == 'Biggest Loss')
].iloc[0]
event_ticker = event_choice['Ticker']
event_date = pd.Timestamp(event_choice['Event_Date'])

calendar_window = pd.Timedelta(days=14)
event_window = long[
    (long['Ticker'] == event_ticker)
    & long['Date'].between(event_date - calendar_window, event_date + calendar_window)
].sort_values('Date').set_index('Date')

ax = event_window['Close'].plot(
    kind='line', marker='o', figsize=(10, 5),
    title=f"{event_ticker}: Event Window Around {event_date.date()}",
    ylabel='Adjusted closing price ($)'
)
ax.axvline(event_date, color='red', linestyle='--', label=event_choice['Type'])
ax.set_xlabel('Date')
ax.legend()
plt.tight_layout()
plt.savefig(f"charts/{event_ticker}_event_window.png", dpi=150)
plt.show()

# Chart 3 : Distribution spread of daily returns of all stocks
Path("charts").mkdir(exist_ok=True)

long["Daily_Return_Pct"] = long["Daily_Return"] * 100  
long.boxplot(column="Daily_Return_Pct", by="Ticker", figsize=(9,5))
plt.title("Daily return distributions by ticker")
plt.suptitle("")
plt.xlabel("Ticker")
plt.ylabel("Daily return (%)")
plt.tight_layout()
plt.savefig("charts/return_distribution.png", dpi=150)
plt.show()

# Chart 4 : Scatter plot of daily returns between CVX and XOM
Path("charts").mkdir(exist_ok=True)

scatter_points = long.pivot(index="Date", columns="Ticker", values="Daily_Return_Pct")

plt.figure(figsize=(7, 5))
plt.scatter(
    scatter_points["CVX"],
    scatter_points["XOM"],
    alpha=0.35,
)
plt.title("Daily return relationship: CVX vs. XOM")
plt.xlabel("CVX daily return (%)")
plt.ylabel("XOM daily return (%)")
plt.tight_layout()
plt.savefig("charts/return_relationship.png", dpi=150)
plt.show()