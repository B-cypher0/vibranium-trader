import MetaTrader5 as mt5
from data_fetch import connect, get_price_volume_data, SYMBOLS
from signals import is_near_psych_level, is_volume_confirming, get_psych_level_range_position
from smc import find_swing_points, detect_bos_choch, find_last_order_block, find_fair_value_gaps


def evaluate_signal(symbol, df):
    """
    Combines trend structure, psychological levels, volume, and
    order blocks/FVG into one signal verdict for a symbol.
    """
    swing_highs, swing_lows = find_swing_points(df)
    structure_signal, trend = detect_bos_choch(df, swing_highs, swing_lows)

    last_price = df['close'].iloc[-1]
    near_level, level = is_near_psych_level(symbol, last_price)
    lower_level, upper_level, range_percent = get_psych_level_range_position(symbol, last_price)
    vol_confirming, current_vol, avg_vol = is_volume_confirming(df)

    direction = None
    if "bullish" in structure_signal:
        direction = "bullish"
    elif "bearish" in structure_signal:
        direction = "bearish"

    ob = find_last_order_block(df, direction) if direction else None
    fvgs = find_fair_value_gaps(df)
    relevant_fvg = None
    if direction and fvgs:
        matching = [f for f in fvgs if f['type'] == direction]
        relevant_fvg = matching[-1] if matching else None

    signal = None
    if direction and near_level and vol_confirming:
        signal = "BUY" if direction == "bullish" else "SELL"

    return {
        'price': last_price,
        'trend': trend,
        'structure_signal': structure_signal,
        'near_psych_level': near_level,
        'psych_level': level,
        'range_lower': lower_level,
        'range_upper': upper_level,
        'range_percent': range_percent,
        'volume_confirming': vol_confirming,
        'current_volume': current_vol,
        'avg_volume': avg_vol,
        'order_block': ob,
        'fair_value_gap': relevant_fvg,
        'signal': signal,
    }


if __name__ == "__main__":
    if connect():
        for symbol in SYMBOLS:
            df = get_price_volume_data(symbol)
            result = evaluate_signal(symbol, df)

            print(f"\n--- {symbol} ---")
            print(f"Price: {result['price']}")
            print(f"Trend: {result['trend']} | Structure: {result['structure_signal']}")
            print(f"Range: {result['range_lower']} -> {result['range_upper']} "
                  f"| {result['range_percent']:.1f}% through")
            print(f"Near psych level: {result['near_psych_level']} (level: {result['psych_level']})")
            print(f"Volume confirming: {result['volume_confirming']} "
                  f"(current: {result['current_volume']}, avg: {result['avg_volume']:.1f})")
            print(f"Order block: {result['order_block']}")
            print(f"Fair value gap: {result['fair_value_gap']}")
            print(f"\n>>> SIGNAL: {result['signal']} <<<")
        mt5.shutdown()