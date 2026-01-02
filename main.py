import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategy import SupertrendStrategy
from src.backtest import run_backtest

def create_mock_data(days=90):
    """
    Creates a mock OHLCV dataset for the Nifty 50 index.
    """
    start_date = pd.to_datetime('2023-01-01')
    total_minutes = days * 375 # 6.25 hours of trading per day
    timestamps = pd.to_datetime(start_date) + pd.to_timedelta(np.arange(total_minutes), 'm')

    # Filter out non-trading hours (before 9:15 and after 15:30)
    timestamps = timestamps[
        (timestamps.time >= pd.to_datetime('09:15').time()) &
        (timestamps.time <= pd.to_datetime('15:30').time())
    ]

    # Filter out weekends
    timestamps = timestamps[timestamps.dayofweek < 5]

    # Resample to 15-minute intervals
    df = pd.DataFrame(index=timestamps)
    df = df.resample('15min').first()

    price = 18000
    prices = []
    for _ in range(len(df)):
        price += np.random.randn() * 5
        prices.append(price)

    df['Open'] = prices
    df['High'] = df['Open'] + np.random.uniform(0, 10, size=len(df))
    df['Low'] = df['Open'] - np.random.uniform(0, 10, size=len(df))
    df['Close'] = df['Open'] + np.random.uniform(-5, 5, size=len(df))
    df['Volume'] = np.random.randint(10000, 50000, size=len(df))

    return df.dropna()

if __name__ == '__main__':
    # Create an instance of the trading strategy
    strategy = SupertrendStrategy(lot_size=1, p=10, m1=1, m2=2)

    # Generate mock historical data
    historical_data = create_mock_data(days=90)

    # Run the backtest
    run_backtest(strategy, historical_data)
