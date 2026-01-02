import pytest
import pandas as pd
from unittest.mock import patch
from src.strategy import SupertrendStrategy

@pytest.fixture
def strategy():
    """Fixture to create a SupertrendStrategy instance for tests."""
    return SupertrendStrategy(lot_size=1, p=10, m1=1, m2=2)

def create_test_data(data_dict, index):
    """Helper function to create a pandas DataFrame for testing."""
    return pd.DataFrame(data_dict, index=pd.to_datetime(index))

def get_prepared_data(data, st1_series, st2_series, st1_value_series):
    """Helper function to create a pre-formatted DataFrame for mocking."""
    prepared_data = data.copy()
    prepared_data['st1'] = st1_series
    prepared_data['st2'] = st2_series
    prepared_data['st1_value'] = st1_value_series
    prepared_data['date'] = prepared_data.index.date
    prepared_data['time'] = prepared_data.index.time
    return prepared_data

def test_strategy_initialization(strategy):
    """Tests the initialization of the SupertrendStrategy class."""
    assert strategy.lot_size == 1
    assert strategy.p == 10
    assert strategy.m1 == 1
    assert strategy.m2 == 2

def test_sell_pe_on_bullish_continuation(strategy):
    """Tests selling a PE on a bullish continuation signal."""
    data = create_test_data({
        'High': [100, 100, 102], 'Low': [90, 90, 92], 'Close': [95, 95, 101],
    }, ['2023-01-01 15:15:00', '2023-01-02 09:30:00', '2023-01-02 09:45:00'])
    prepared_data = get_prepared_data(data, [True, True, True], [True, True, True], [98, 98, 98])

    with patch.object(strategy, '_prepare_data', return_value=prepared_data):
        signals = strategy.generate_signals(data)

    assert len(signals) == 1
    assert signals[0]['action'] == 'SELL_PE'
    assert signals[0]['timestamp'] == pd.to_datetime('2023-01-02 09:45:00')

def test_sell_ce_on_bearish_continuation(strategy):
    """Tests selling a CE on a bearish continuation signal."""
    data = create_test_data({
        'High': [100, 100, 90], 'Low': [90, 90, 80], 'Close': [95, 95, 85],
    }, ['2023-01-01 15:15:00', '2023-01-02 09:30:00', '2023-01-02 09:45:00'])
    prepared_data = get_prepared_data(data, [False, False, False], [False, False, False], [102, 102, 102])

    with patch.object(strategy, '_prepare_data', return_value=prepared_data):
        signals = strategy.generate_signals(data)

    assert len(signals) == 1
    assert signals[0]['action'] == 'SELL_CE'
    assert signals[0]['timestamp'] == pd.to_datetime('2023-01-02 09:45:00')

def test_sell_pe_on_st1_flip_to_bullish(strategy):
    """Tests selling a PE when the ST1 indicator flips to bullish."""
    data = create_test_data({
        'High': [100, 102], 'Low': [90, 92], 'Close': [95, 101],
    }, ['2023-01-02 09:30:00', '2023-01-02 09:45:00'])
    prepared_data = get_prepared_data(data, [False, True], [False, True], [102, 98])

    with patch.object(strategy, '_prepare_data', return_value=prepared_data):
        signals = strategy.generate_signals(data)

    assert len(signals) == 1
    assert signals[0]['action'] == 'SELL_PE'

def test_sell_ce_on_st1_flip_to_bearish(strategy):
    """Tests selling a CE when the ST1 indicator flips to bearish."""
    data = create_test_data({
        'High': [100, 90], 'Low': [90, 80], 'Close': [95, 85],
    }, ['2023-01-02 09:30:00', '2023-01-02 09:45:00'])
    prepared_data = get_prepared_data(data, [True, False], [True, False], [98, 102])

    with patch.object(strategy, '_prepare_data', return_value=prepared_data):
        signals = strategy.generate_signals(data)

    assert len(signals) == 1
    assert signals[0]['action'] == 'SELL_CE'

def test_exit_and_reenter_on_sl_hit(strategy):
    """Tests that an exit is triggered by SL and a new trade is entered on the same candle."""
    data = create_test_data({
        'High': [100, 102, 90], 'Low': [90, 92, 80], 'Close': [95, 101, 85],
    }, ['2023-01-02 09:30:00', '2023-01-02 09:45:00', '2023-01-02 10:00:00'])
    prepared_data = get_prepared_data(data, [False, True, False], [False, True, False], [102, 98, 102])

    with patch.object(strategy, '_prepare_data', return_value=prepared_data):
        signals = strategy.generate_signals(data)

    assert len(signals) == 3
    assert signals[0]['action'] == 'SELL_PE'
    assert signals[1]['action'] == 'EXIT'
    assert signals[1]['reason'] == 'SL Hit'
    assert signals[2]['action'] == 'SELL_CE'

def test_exit_on_square_off_time(strategy):
    """Tests exiting a position at the square-off time."""
    data = create_test_data({
        'High': [100, 102, 103], 'Low': [90, 92, 93], 'Close': [95, 101, 102],
    }, ['2023-01-02 14:00:00', '2023-01-02 14:15:00', '2023-01-02 15:16:00'])
    prepared_data = get_prepared_data(data, [False, True, True], [False, True, True], [102, 98, 99])

    with patch.object(strategy, '_prepare_data', return_value=prepared_data):
        signals = strategy.generate_signals(data)

    assert len(signals) == 2
    assert signals[0]['action'] == 'SELL_PE'
    assert signals[1]['action'] == 'EXIT'
    assert signals[1]['reason'] == 'Timed Square Off'

def test_exit_at_end_of_day(strategy):
    """Tests exiting a position at the end of the day."""
    data = create_test_data({
        'High': [100, 102, 103], 'Low': [90, 92, 93], 'Close': [95, 101, 102],
    }, ['2023-01-02 14:00:00', '2023-01-02 14:15:00', '2023-01-03 09:15:00'])
    prepared_data = get_prepared_data(data, [False, True, True], [False, True, True], [102, 98, 99])

    with patch.object(strategy, '_prepare_data', return_value=prepared_data):
        signals = strategy.generate_signals(data)

    assert len(signals) == 2
    assert signals[0]['action'] == 'SELL_PE'
    assert signals[1]['action'] == 'EXIT'
    assert signals[1]['reason'] == 'EOD Square Off'
