import MetaTrader5 as mt5

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

symbols = mt5.symbols_get()
if symbols is None:
    print("No symbols returned, error:", mt5.last_error())
else:
    keywords = ["US30", "XAU", "JPY"]
    print("Matching symbols found:\n")
    for s in symbols:
        if any(k in s.name.upper() for k in keywords):
            print(s.name)

mt5.shutdown()