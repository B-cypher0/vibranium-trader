import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

SYMBOLS = ["US30.cent", "XAUUSD.cent", "USDJPY.cent"]

def connect():
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return False
    return True

def get_price_volume_data(symbol, timeframe=mt5.TIMEFRAME_M15, bars=200):
    """
    Pulls recent candle data including price and volume for a given symbol.
    """
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}, error: {mt5.last_error()}")
        return None

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None:
        print(f"Failed to get data for {symbol}, error: {mt5.last_error()}")
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def get_all_symbols_data():
    data = {}
    for symbol in SYMBOLS:
        df = get_price_volume_data(symbol)
        if df is not None:
            data[symbol] = df
    return data

if __name__ == "__main__":
    if connect():
        all_data = get_all_symbols_data()
        for symbol, df in all_data.items():
            print(f"\n--- {symbol} ---")
            print(df.tail(5))
        mt5.shutdown()