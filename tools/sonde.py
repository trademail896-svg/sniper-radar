"""Diagnostic Bitget : champs du ticker, des marchés et profondeur des bougies."""
import ccxt, json
ex = ccxt.bitget({"options": {"defaultType": "swap"}, "enableRateLimit": True})
ex.load_markets()
m = ex.markets["BTC/USDT:USDT"]
print("MARCHE info:", json.dumps(m["info"])[:900])
t = ex.fetch_tickers()
d = t["BTC/USDT:USDT"]
print("TICKER:", {k: d[k] for k in ("last", "percentage", "baseVolume", "quoteVolume")})
print("TICKER info:", json.dumps(d["info"])[:900])
qv = sorted(((v.get("quoteVolume") or 0) for k, v in t.items() if k.endswith(":USDT")), reverse=True)
print("quoteVolume rang 1/50/100/200:", [round(qv[i] / 1e6, 1) for i in (0, 49, 99, 199) if i < len(qv)])
for tf, lim in (("4h", 600), ("1h", 300)):
    o = ex.fetch_ohlcv("ETH/USDT:USDT", tf, limit=lim)
    print(tf, "demandé", lim, "reçu", len(o))
lt = [x["info"].get("launchTime") for x in ex.markets.values() if x.get("swap")][:10]
print("launchTime échantillon:", lt)
