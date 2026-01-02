import pandas as pd
import numpy as np
from src.indicators import calculate_supertrend

class SupertrendStrategy:
    def __init__(self, lot_size=1, p=10, m1=1, m2=2):
        """
        Initializes the Supertrend trading strategy.
        :param lot_size: The number of lots to trade.
        :param p: The ATR period for the Supertrend indicators.
        :param m1: The multiplier for the primary Supertrend indicator.
        :param m2: The multiplier for the secondary Supertrend indicator (for stop loss).
        """
        self.lot_size = lot_size
        self.p = p
        self.m1 = m1
        self.m2 = m2
        self.position = None
        self.first_candle_logic_executed_today = False
        self.first_candle_high = None
        self.first_candle_low = None
        self.previous_day_st1_is_bullish = None

    def _prepare_data(self, data):
        """
        Prepares historical data by calculating Supertrend indicators.
        """
        df = data.copy()
        st1_df = calculate_supertrend(df, period=self.p, multiplier=self.m1)
        df['st1'] = st1_df['Supertrend']
        df['st1_value'] = np.where(df['st1'], st1_df['Final Lowerband'], st1_df['Final Upperband'])
        st2_df = calculate_supertrend(df, period=self.p, multiplier=self.m2)
        df['st2'] = st2_df['Supertrend']
        df['date'] = df.index.date
        df['time'] = df.index.time
        return df

    def generate_signals(self, data):
        """
        Generates trading signals for the entire historical dataset.
        """
        df = self._prepare_data(data)
        signals = []
        if df.empty:
            return signals

        first_day_data = df[df['date'] == df['date'].iloc[0]]
        if not first_day_data.empty:
            self.previous_day_st1_is_bullish = first_day_data.iloc[-1]['st1']

        for i in range(1, len(df)):
            prev_row = df.iloc[i-1]
            current_row = df.iloc[i]

            if current_row['date'] != prev_row['date']:
                self.first_candle_logic_executed_today = False
                self.first_candle_high = None
                self.first_candle_low = None
                self.previous_day_st1_is_bullish = prev_row['st1']
                if self.position:
                    signals.append({'timestamp': prev_row.name, 'action': 'EXIT', 'reason': 'EOD Square Off'})
                    self.position = None

            is_entry_time = pd.to_datetime('09:30').time() <= current_row['time'] <= pd.to_datetime('15:01').time()
            is_square_off_time = current_row['time'] >= pd.to_datetime('15:16').time()

            if self.position and is_square_off_time:
                signals.append({'timestamp': current_row.name, 'action': 'EXIT', 'reason': 'Timed Square Off'})
                self.position = None
                continue

            # In a backtest, intra-candle SL is checked at the close of the candle.
            if self.position == 'PE_SOLD' and (not current_row['st1'] or not current_row['st2']):
                signals.append({'timestamp': current_row.name, 'action': 'EXIT', 'reason': 'SL Hit'})
                self.position = None
            elif self.position == 'CE_SOLD' and (current_row['st1'] or current_row['st2']):
                signals.append({'timestamp': current_row.name, 'action': 'EXIT', 'reason': 'SL Hit'})
                self.position = None

            if self.position or not is_entry_time:
                continue

            if current_row['time'] == pd.to_datetime('09:30').time():
                self.first_candle_high = current_row['High']
                self.first_candle_low = current_row['Low']

            if not self.first_candle_logic_executed_today and self.first_candle_high is not None:
                is_bullish_continuation = current_row['st1'] and self.previous_day_st1_is_bullish
                if is_bullish_continuation and current_row['Close'] > self.first_candle_high:
                    signals.append({'timestamp': current_row.name, 'action': 'SELL_PE', 'strike': current_row['st1_value']})
                    self.position = 'PE_SOLD'
                    self.first_candle_logic_executed_today = True
                    continue

                is_bearish_continuation = not current_row['st1'] and not self.previous_day_st1_is_bullish
                if is_bearish_continuation and current_row['Close'] < self.first_candle_low:
                    signals.append({'timestamp': current_row.name, 'action': 'SELL_CE', 'strike': current_row['st1_value']})
                    self.position = 'CE_SOLD'
                    self.first_candle_logic_executed_today = True
                    continue

            st1_flipped_to_bullish = current_row['st1'] and not prev_row['st1']
            if st1_flipped_to_bullish:
                signals.append({'timestamp': current_row.name, 'action': 'SELL_PE', 'strike': current_row['st1_value']})
                self.position = 'PE_SOLD'
                continue

            st1_flipped_to_bearish = not current_row['st1'] and prev_row['st1']
            if st1_flipped_to_bearish:
                signals.append({'timestamp': current_row.name, 'action': 'SELL_CE', 'strike': current_row['st1_value']})
                self.position = 'CE_SOLD'
                continue

        return signals

    def execute_trade(self, signal):
        """
        Executes a trade based on the given signal. (For live trading)
        """
        pass
