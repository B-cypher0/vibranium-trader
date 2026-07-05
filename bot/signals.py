from data_fetch import connect, get_price_volume_data
import MetaTrader5 as mt5

# Psychological level intervals per symbol
LEVEL_INTERVALS = {
    "US30.cent": 500,
    "XAUUSD.cent": 500,
    "USDJPY.cent": 5,
}

# How close price needs to be to count as "near" a level — tweak these as you backtest
PROXIMITY_THRESHOLD = {
    "US30.cent": 80,      # index points
    "XAUUSD.cent": 8,     # price points
    "USDJPY.cent": 0.15,  # yen (~15 pips)
}

def get_nearest_psych_level(symbol, price):
    """
    Finds the closest round-number level to the current price.
    Returns (level, distance).
    """
    interval = LEVEL_INTERVALS.get(symbol)
    if interval is None:
        return None, None

    lower_level = (price // interval) * interval
    upper_level = lower_level + interval

    dist_to_lower = price - lower_level
    dist_to_upper = upper_level - price

    if dist_to_lower <= dist_to_upper:
        return lower_level, dist_to_lower
    return upper_level, dist_to_upper

def is_near_psych_level(symbol, price):
    """
    Returns (True/False, level) — whether price is within the
    proximity threshold of a psychological level right now.
    """
    level, distance = get_nearest_psych_level(symbol, price)
    if level is None:
        return False, None
    threshold = PROXIMITY_THRESHOLD.get(symbol, 0)
    return distance <= threshold, level

def get_psych_level_range_position(symbol, price):
    """
    Returns (lower_level, upper_level, percent_through_range) — where
    percent_through_range is 0% right at the lower level and 100%
    right at the upper level.
    """
    interval = LEVEL_INTERVALS.get(symbol)
    if interval is None:
        return None, None, None

    lower_level = (price // interval) * interval
    upper_level = lower_level + interval
    percent_through = ((price - lower_level) / interval) * 100

    return lower_level, upper_level, percent_through

def is_volume_confirming(df, multiplier=1.5, avg_window=20):
    """
    Checks whether the most recent candle's volume is significantly
    above the recent average.
    Returns (True/False, current_volume, recent_avg_volume).
    """
    if len(df) < avg_window + 1:
        return False, None, None

    recent_avg = df['tick_volume'].iloc[-(avg_window + 1):-1].mean()
    current_volume = df['tick_volume'].iloc[-1]

    is_confirming = current_volume >= recent_avg * multiplier
    return is_confirming, current_volume, recent_avg


if __name__ == "__main__":
    if connect():
        for symbol in ["XAUUSD.cent", "US30.cent", "USDJPY.cent"]:
            df = get_price_volume_data(symbol)
            last_price = df['close'].iloc[-1]

            near, level = is_near_psych_level(symbol, last_price)
            lower, upper, percent = get_psych_level_range_position(symbol, last_price)
            confirming, current_vol, avg_vol = is_volume_confirming(df)

            print(f"\n--- {symbol} ---")
            print(f"Last price: {last_price}")
            print(f"Near psych level: {near} (level: {level})")
            print(f"Range position: {lower} -> {upper} | {percent:.1f}% through")
            print(f"Volume confirming: {confirming} (current: {current_vol}, avg: {avg_vol:.1f})")
        mt5.shutdown()