"""Teste quelles plateformes répondent depuis les serveurs GitHub (tickers, bougies 4H, OI)."""
import ccxt, time
TESTS = [
    ("bybit (bytick.com)", lambda: ccxt.bybit({"hostname": "bytick.com", "options": {"defaultType": "swap", "defaultSubType": "linear"}}), "BTC/USDT:USDT"),
    ("bitget", lambda: ccxt.bitget({"options": {"defaultType": "swap"}}), "BTC/USDT:USDT"),
    ("okx", lambda: ccxt.okx({"options": {"defaultType": "swap"}}), "BTC/USDT:USDT"),
    ("blofin", lambda: ccxt.blofin({"options": {"defaultType": "swap"}}), "BTC/USDT:USDT"),
    ("mexc", lambda: ccxt.mexc({"options": {"defaultType": "swap"}}), "BTC/USDT:USDT"),
    ("gate", lambda: ccxt.gate({"options": {"defaultType": "swap"}}), "BTC/USDT:USDT"),
    ("kucoinfutures", lambda: ccxt.kucoinfutures(), "BTC/USDT:USDT"),
]
for nom, mk, sym in TESTS:
    r = []
    try:
        ex = mk(); t0 = time.time()
        ex.load_markets()
        perps = [m for m in ex.markets.values() if m.get("swap") and m.get("linear") and m.get("quote") == "USDT"]
        r.append(f"marchés {len(perps)}")
        tf = ["XAU", "TSLA", "NVDA", "SPX", "XAG", "CL", "WTI", "QQQ"]
        r.append("tradfi " + ",".join(b for b in tf if any(m["base"] in (b, b + "T") for m in perps)))
        tk = ex.fetch_tickers([sym]) if nom.startswith(("okx","mexc")) else ex.fetch_tickers()
        r.append(f"tickers {len(tk)}")
        o = ex.fetch_ohlcv(sym, "4h", limit=200); r.append(f"4h {len(o)}")
        try:
            oi = ex.fetch_open_interest_history(sym, "1h", limit=25); r.append(f"OI hist {len(oi)}")
        except Exception as e:
            r.append("OI hist NON (" + type(e).__name__ + ")")
        try:
            f = ex.fetch_funding_rate(sym); r.append("funding ok")
        except Exception as e:
            r.append("funding NON")
        r.append(f"{time.time()-t0:.1f}s")
        print(f"OK   {nom:20} " + " · ".join(r))
    except Exception as e:
        print(f"BLOQUÉ {nom:18} " + " · ".join(r) + f" → {type(e).__name__}: {str(e)[:120]}")
