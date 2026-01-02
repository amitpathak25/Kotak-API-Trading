import pandas as pd
from src.strategy import SupertrendStrategy

def run_backtest(strategy, historical_data):
    """
    Runs a backtest of the trading strategy.

    This function simulates the execution of a trading strategy on historical data.
    It generates signals, tracks trades, and provides a summary of the strategy's
    performance.

    NOTE: This backtest does not calculate Profit and Loss (PnL) because it
    operates on the Nifty 50 index data, not on historical options data.
    Accurate PnL calculation for options strategies requires historical
    options premium data, which is not available in this backtest. Instead,
    this function logs the signals and the market conditions at the time of the
    trade to help evaluate the strategy's logic.
    """
    signals = strategy.generate_signals(historical_data)

    if not signals:
        print("No trades were generated during the backtest.")
        return

    trades = []

    for i in range(len(signals)):
        signal = signals[i]
        action = signal['action']

        if 'SELL' in action:
            entry_timestamp = signal['timestamp']
            entry_price = historical_data.loc[entry_timestamp]['Close']
            strike_price = signal['strike']

            exit_signal = None
            for j in range(i + 1, len(signals)):
                if signals[j]['action'] == 'EXIT':
                    exit_signal = signals[j]
                    break

            if exit_signal:
                exit_timestamp = exit_signal['timestamp']
                exit_price = historical_data.loc[exit_timestamp]['Close']
                exit_reason = exit_signal.get('reason', 'Unknown')

                # Determine the outcome based on the underlying's price movement
                if action == 'SELL_PE':
                    outcome = 'Win' if exit_price > strike_price else 'Loss'
                else: # SELL_CE
                    outcome = 'Win' if exit_price < strike_price else 'Loss'

                trades.append({
                    'entry_action': action,
                    'entry_time': entry_timestamp,
                    'entry_price_underlying': entry_price,
                    'strike_price': strike_price,
                    'exit_time': exit_timestamp,
                    'exit_price_underlying': exit_price,
                    'exit_reason': exit_reason,
                    'outcome': outcome
                })

    if not trades:
        print("No completed trades were made during the backtest.")
        return

    results = pd.DataFrame(trades)

    print("--- Backtest Signal Log ---")
    print(f"Total Trades Logged: {len(results)}")
    if not results.empty:
        win_rate = (results['outcome'] == 'Win').sum() / len(results) * 100
        print(f"Win Rate: {win_rate:.2f}%")
    print("\n--- Trade Log ---")
    print(results)
