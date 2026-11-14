"""
SNIPER RADAR — Collecte (CCXT, API publiques, sans clé)
============================================================
- Liste des perps USDT linéaires (avec date de lancement)
- Ticker 24 h de tous les contrats en un seul appel (variation, volume USDT,
  funding, open interest)
- Bougies 1H et 4H clôturées, en parallèle
- Historique d'OI 24 h (plateforme OI), seulement pour les candidats notés
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import ccxt
import numpy as np

from . import config

_OPTIONS = {"defaultType": "swap", "defaultSubType": "linear"}
_local = threading.local()
_MARCHES = None


def _nouvel_exchange(nom=None):
    klass = getattr(ccxt, nom or config.PLATEFORME)
    return klass({"enableRateLimit": True, "rateLimit": config.RATE_LIMIT_MS, "timeout": 30000,
                  "options": dict(_OPTIONS)})


def _exchange():
    ex = getattr(_local, "ex", None)
    if ex is None:
        ex = _nouvel_exchange()
        if _MARCHES is not None:
            ex.set_markets(list(_MARCHES.values()))
        _local.ex = ex
    return ex


def _f(x, defaut=np.nan):
    try:
        return float(x)
    except (TypeError, ValueError):
        return defaut


def charger_marches():
    """Retourne la liste des perps USDT linéaires actifs : dicts symbol/base/launch_ms."""
    global _MARCHES
    ex = _nouvel_exchange()
    ex.load_markets()
    _MARCHES = ex.markets
    _local.ex = ex
    res = []
    for m in ex.markets.values():
        if not (m.get("swap") and m.get("linear") and m.get("quote") == "USDT"
                and m.get("settle") == "USDT" and m.get("active", True)):
            continue
        info = m.get("info") or {}
        statut = str(info.get("status") or info.get("symbolStatus") or "normal").lower()
        if statut not in ("trading", "normal", "live", "open"):
            continue
        res.append({
            "symbol": m["symbol"],
            "id": m["id"],
            "base": m["base"],
            "launch_ms": int(_f(info.get("launchTime"), 0) or 0),
        })
    return res


def charger_tickers():
    """symbol → {last, pct24, qv24, funding, oi_valeur}."""
    ex = _exchange()
    t = ex.fetch_tickers()
    out = {}
    for sym, d in t.items():
        info = d.get("info") or {}
        last = _f(d.get("last"))
        pct = d.get("percentage")
        if pct is None:
            pct = _f(info.get("change24h", info.get("price24hPcnt"))) * 100.0
        qv = d.get("quoteVolume")
        if qv is None:
            qv = info.get("usdtVolume", info.get("quoteVolume", info.get("turnover24h")))
        oi_val = _f(info.get("openInterestValue"))
        if np.isnan(oi_val):
            oi_val = _f(info.get("holdingAmount"), 0.0) * (last if not np.isnan(last) else 0.0)
        out[sym] = {
            "last": last,
            "pct24": _f(pct),
            "qv24": _f(qv, 0.0),
            "funding": _f(info.get("fundingRate")),
            "oi_valeur": oi_val,
        }
    return out


_TF_MS = {"1h": 3_600_000, "4h": 14_400_000}


def _bougies(symbol, tf, limite):
    ex = _exchange()
    for essai in range(3):
        try:
            raw = ex.fetch_ohlcv(symbol, timeframe=tf, limit=limite)
            break
        except (ccxt.NetworkError, ccxt.ExchangeError):
            if essai == 2:
                return None
            time.sleep(1.5 * (essai + 1))
    if not raw:
        return None
    a = np.array(raw, dtype=float)
    maintenant = time.time() * 1000
    if a[-1, 0] + _TF_MS[tf] > maintenant:          # retire la bougie non clôturée
        a = a[:-1]
    if len(a) < 60:
        return None
    return {"t": a[:, 0].astype(np.int64), "o": a[:, 1], "h": a[:, 2], "l": a[:, 3], "c": a[:, 4],
            "v": a[:, 5]}


def charger_bougies(symboles):
    """symbol → {'1h': bougies, '4h': bougies} (tokens en échec retirés)."""
    res = {}
    echecs = []

    def job(sym):
        b1 = _bougies(sym, "1h", config.NB_BOUGIES_1H)
        b4 = _bougies(sym, "4h", config.NB_BOUGIES_4H)
        return sym, b1, b4

    with ThreadPoolExecutor(max_workers=config.WORKERS) as pool:
        futs = [pool.submit(job, s) for s in symboles]
        for i, f in enumerate(as_completed(futs), 1):
            try:
                sym, b1, b4 = f.result()
            except Exception:
                continue
            if b1 is None or b4 is None:
                echecs.append(sym)
            else:
                res[sym] = {"1h": b1, "4h": b4}
            if i % 50 == 0:
                print(f"[données] {i}/{len(symboles)} tokens")
    if echecs:
        print(f"[données] {len(echecs)} échecs : {echecs[:20]}")
    return res


def variation_oi_24h(symboles):
    """symbol → variation % de l'open interest sur 24 h (candidats seulement)."""
    out = {}

    ex_oi = _nouvel_exchange(config.PLATEFORME_OI)
    try:
        ex_oi.load_markets()
    except Exception:
        return {s: np.nan for s in symboles}
    verrou = threading.Lock()

    def job(sym):
        if sym not in ex_oi.markets:
            return sym, np.nan
        try:
            with verrou:
                h = ex_oi.fetch_open_interest_history(sym, "1h", limit=25)
        except Exception:
            return sym, np.nan
        vals = [_f(x.get("openInterestAmount")) for x in h if x]
        vals = [v for v in vals if not np.isnan(v)]
        if len(vals) < 2 or vals[0] == 0:
            return sym, np.nan
        return sym, (vals[-1] - vals[0]) / vals[0] * 100.0

    with ThreadPoolExecutor(max_workers=config.WORKERS) as pool:
        for sym, v in pool.map(job, symboles):
            out[sym] = v
    return out
