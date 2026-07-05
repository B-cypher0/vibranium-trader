import requests

NTFY_TOPIC = "vibranium-xk92mfp4q1"  
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"


def send_notification(title, message, priority="default", tags=None):
    """
    Sends a push notification via ntfy.sh to whatever devices are
    subscribed to NTFY_TOPIC.
    priority: min, low, default, high, urgent
    tags: list of emoji-shortcode strings, e.g. ["chart_with_upwards_trend"]
    """
    headers = {
        "Title": title,
        "Priority": priority,
    }
    if tags:
        headers["Tags"] = ",".join(tags)

    try:
        response = requests.post(NTFY_URL, data=message.encode('utf-8'), headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return False


def send_signal_alert(symbol, result):
    """
    Formats a signal result dict (from evaluate_signal) into a
    readable notification and sends it.
    """
    signal = result['signal']
    if not signal:
        return False

    tag = "chart_with_upwards_trend" if signal == "BUY" else "chart_with_downwards_trend"
    title = f"{signal} signal - {symbol}"

    message = (
        f"Price: {result['price']}\n"
        f"Trend: {result['trend']}\n"
        f"Structure: {result['structure_signal']}\n"
        f"Near level: {result['psych_level']}\n"
        f"Volume: {result['current_volume']} (avg {result['avg_volume']:.1f})"
    )

    return send_notification(title, message, priority="high", tags=[tag])


if __name__ == "__main__":
    # Dummy signal so you can confirm your phone actually receives it
    # before this is wired into the real bot.
    test_result = {
        'signal': 'BUY',
        'price': 4174.81,
        'trend': 'uptrend',
        'structure_signal': 'BOS bullish (continuation)',
        'psych_level': 4000.0,
        'current_volume': 3200,
        'avg_volume': 2100.0,
    }
    success = send_signal_alert("XAUUSD.cent (TEST)", test_result)
    print("Notification sent!" if success else "Notification failed.")