"""Diagnostic : ordre et contenu des bougies BloFin vs Bitget."""
import ccxt, time
for nom in ("blofin", "bitget"):
    ex = getattr(ccxt, nom)({"options": {"defaultType": "swap"}})
    o = ex.fetch_ohlcv("BTC/USDT:USDT", "4h", limit=600)
    t = [x[0] for x in o]
    croissant = all(t[i] < t[i + 1] for i in range(len(t) - 1))
    print(f"{nom}: {len(o)} bougies · croissant={croissant} · 1re={time.strftime('%Y-%m-%d %H:%M', time.gmtime(t[0]/1000))} · dern={time.strftime('%Y-%m-%d %H:%M', time.gmtime(t[-1]/1000))} · close dern={o[-1][4]}")
    print("   5 dernières:", [(time.strftime('%d %H:%M', time.gmtime(x[0]/1000)), x[4]) for x in o[-5:]])
