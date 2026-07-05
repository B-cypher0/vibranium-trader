from data_fetch import connect, get_price_volume_data
import MetaTrader5 as mt5


def find_swing_points(df, lookback=2):
    """
    Identifies swing highs and lows using a fractal method.
    Returns two lists of (index, price) tuples.
    """
    swing_highs = []
    swing_lows = []

    for i in range(lookback, len(df) - lookback):
        window_high = df['high'].iloc[i - lookback:i + lookback + 1]
        window_low = df['low'].iloc[i - lookback:i + lookback + 1]

        if df['high'].iloc[i] == window_high.max():
            swing_highs.append((i, df['high'].iloc[i]))

        if df['low'].iloc[i] == window_low.min():
            swing_lows.append((i, df['low'].iloc[i]))

    return swing_highs, swing_lows


def detect_trend_structure(swing_highs, swing_lows):
    """
    Compares the last two swing highs against each other, and the last
    two swing lows against each other, independently.
    Higher high + higher low = uptrend.
    Lower high + lower low = downtrend.
    Otherwise = ranging.
    """
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "insufficient data"

    last_high, prev_high = swing_highs[-1][1], swing_highs[-2][1]
    last_low, prev_low = swing_lows[-1][1], swing_lows[-2][1]

    if last_high > prev_high and last_low > prev_low:
        return "uptrend"
    if last_high < prev_high and last_low < prev_low:
        return "downtrend"
    return "ranging"


def detect_bos_choch(df, swing_highs, swing_lows):
    """
    Compares latest close against the most recent swing high/low
    to flag a Break of Structure (continuation) or
    Change of Character (potential reversal).
    """
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "insufficient data", None

    trend = detect_trend_structure(swing_highs, swing_lows)
    last_close = df['close'].iloc[-1]
    last_high = swing_highs[-1][1]
    last_low = swing_lows[-1][1]

    if trend == "uptrend":
        if last_close > last_high:
            return "BOS bullish (continuation)", trend
        if last_close < last_low:
            return "CHoCH bearish (potential reversal)", trend

    elif trend == "downtrend":
        if last_close < last_low:
            return "BOS bearish (continuation)", trend
        if last_close > last_high:
            return "CHoCH bullish (potential reversal)", trend

    return "no break yet", trend


def find_last_order_block(df, direction):
    """
    Walks backward from the current candle to find the last opposing
    candle before the breakout move — this candle is the order block.
    direction: 'bullish' or 'bearish'
    """
    break_index = len(df) - 1
    for i in range(break_index - 1, 0, -1):
        is_bearish_candle = df['close'].iloc[i] < df['open'].iloc[i]
        is_bullish_candle = df['close'].iloc[i] > df['open'].iloc[i]

        if direction == 'bullish' and is_bearish_candle:
            return {
                'time': df['time'].iloc[i],
                'type': 'bullish_ob',
                'top': df['high'].iloc[i],
                'bottom': df['low'].iloc[i],
            }
        if direction == 'bearish' and is_bullish_candle:
            return {
                'time': df['time'].iloc[i],
                'type': 'bearish_ob',
                'top': df['high'].iloc[i],
                'bottom': df['low'].iloc[i],
            }
    return None


def find_fair_value_gaps(df, lookback_candles=50):
    """
    Detects 3-candle Fair Value Gaps (imbalances) in the most recent candles.
    Bullish FVG: candle[i-2].high < candle[i].low
    Bearish FVG: candle[i-2].low > candle[i].high
    """
    fvgs = []
    start = max(2, len(df) - lookback_candles)
    for i in range(start, len(df)):
        c1_high = df['high'].iloc[i - 2]
        c1_low = df['low'].iloc[i - 2]
        c3_high = df['high'].iloc[i]
        c3_low = df['low'].iloc[i]

        if c1_high < c3_low:
            fvgs.append({
                'time': df['time'].iloc[i],
                'type': 'bullish',
                'top': c3_low,
                'bottom': c1_high,
            })
        elif c1_low > c3_high:
            fvgs.append({
                'time': df['time'].iloc[i],
                'type': 'bearish',
                'top': c1_low,
                'bottom': c3_high,
            })
    return fvgs


if __name__ == "__main__":
    if connect():
        df = get_price_volume_data("XAUUSD.cent")
        mt5.shutdown()

        swing_highs, swing_lows = find_swing_points(df)
        print(f"Found {len(swing_highs)} swing highs and {len(swing_lows)} swing lows")

        signal, trend = detect_bos_choch(df, swing_highs, swing_lows)
        print(f"\nCurrent trend: {trend}")
        print(f"Structure signal: {signal}")

        if "bullish" in signal:
            ob = find_last_order_block(df, 'bullish')
        elif "bearish" in signal:
            ob = find_last_order_block(df, 'bearish')
        else:
            ob = None
        print(f"\nActive order block: {ob}")

        fvgs = find_fair_value_gaps(df)
        print(f"\nFound {len(fvgs)} fair value gaps in recent candles")
        print("Last 3 FVGs:")
        for gap in fvgs[-3:]:
            print(f"  {gap['time']} -> {gap['type']} | zone: {gap['bottom']:.2f} - {gap['top']:.2f}")