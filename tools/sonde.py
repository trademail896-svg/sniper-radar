"""Diagnostic : contrats Bitget marqués isRwa, avec leur volume 24 h."""
import ccxt
ex = ccxt.bitget({"options": {"defaultType": "swap"}, "enableRateLimit": True})
ex.load_markets()
t = ex.fetch_tickers()
rwa = []
for m in ex.markets.values():
    if m.get("swap") and m.get("quote") == "USDT" and str(m["info"].get("isRwa")).upper() == "YES":
        rwa.append((t.get(m["symbol"], {}).get("quoteVolume") or 0, m["base"]))
rwa.sort(reverse=True)
print("NB_RWA", len(rwa), "≥1M$:", sum(v >= 1e6 for v, _ in rwa), "≥3M$:", sum(v >= 3e6 for v, _ in rwa))
print("TOP", " ".join(f"{b}:{v/1e6:.1f}" for v, b in rwa[:120]))
cr = sorted(((t.get(m["symbol"], {}).get("quoteVolume") or 0, m["base"]) for m in ex.markets.values()
             if m.get("swap") and m.get("quote") == "USDT" and str(m["info"].get("isRwa")).upper() != "YES"), reverse=True)
print("CRYPTO ≥3M$:", sum(v >= 3e6 for v, _ in cr), " ".join(b for v, b in cr[:60]))
