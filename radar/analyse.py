"""
SNIPER RADAR — Calculs par token
================================
Pour chaque token : EMA50 4H, MSO 4H, RSI 1H + divergence, BB 4H (touches des
6 dernières bougies), compression 90 jours, marché fermé (TradFi).
"""
import numpy as np

from . import config
from . import indicateurs as ind


def _bb_touche(b4, i, mid, up, lo):
    """Décrit une touche de bande sur la bougie 4H d'indice i, ou None."""
    h, l, c = b4["h"][i], b4["l"][i], b4["c"][i]
    if np.isnan(up[i]) or np.isnan(lo[i]):
        return None
    j = i - config.BB_PENTE_BOUGIES
    pente = abs(mid[i] - mid[j]) / mid[j] * 100.0 if j >= 0 and mid[j] else np.nan
    a_plat = (not np.isnan(pente)) and pente <= config.BB_PENTE_MAX_PCT
    if h >= up[i]:
        meche = (h - up[i]) / up[i] * 100.0
        dedans = c <= up[i]
        return {"cote": "haut", "sens": "short", "meche": meche, "dedans": dedans, "a_plat": a_plat}
    if l <= lo[i]:
        meche = (lo[i] - l) / lo[i] * 100.0
        dedans = c >= lo[i]
        return {"cote": "bas", "sens": "long", "meche": meche, "dedans": dedans, "a_plat": a_plat}
    return None


def analyser(b):
    """b = {'1h': bougies, '4h': bougies} → dict de mesures."""
    b1, b4 = b["1h"], b["4h"]
    out = {}

    # ─── EMA50 4H ────────────────────────────────────────────────────────────
    e50 = ind.ema(b4["c"], config.EMA_LONGUEUR)
    out["ema50_4h"] = float(e50[-1])
    out["close_4h"] = float(b4["c"][-1])
    k = config.BTC_PENTE_BOUGIES
    out["ema50_pente"] = float(e50[-1] - e50[-1 - k]) if len(e50) > k else np.nan

    # ─── MSO 4H ──────────────────────────────────────────────────────────────
    if config.MSO_SUR_HEIKIN_ASHI:
        o, h, l, c = ind.heikin_ashi(b4["o"], b4["h"], b4["l"], b4["c"])
    else:
        o, h, l, c = b4["o"], b4["h"], b4["l"], b4["c"]
    m = ind.mso(o, h, l, c, config.MSO_POIDS, config.MSO_LISSAGE)
    out["mso4h"] = float(m[-1]) if not np.isnan(m[-1]) else np.nan
    out["mso4h_prec"] = float(m[-2]) if len(m) > 1 and not np.isnan(m[-2]) else np.nan

    # ─── RSI 1H + divergence ────────────────────────────────────────────────
    r = ind.rsi(b1["c"], config.RSI_LONGUEUR)
    out["div"] = ind.divergence_rsi(b1["h"], b1["l"], r, config.DIV_PIVOT_GAUCHE,
                                    config.DIV_PIVOT_DROITE, config.DIV_FENETRE_1H)

    # ─── BB 4H : touche la plus récente dans les 6 dernières bougies ────────
    mid, up, lo = ind.bollinger(b4["c"], config.BB_LONGUEUR, config.BB_MULT)
    n4 = len(b4["c"])
    out["bb"] = None
    for back in range(config.BB_TOUCHE_BOUGIES):
        i = n4 - 1 - back
        t = _bb_touche(b4, i, mid, up, lo)
        if t:
            t["bougies_depuis"] = back
            t["ts"] = int(b4["t"][i])
            if t["meche"] > config.BB_MECHE_TENDANCE or not t["dedans"]:
                t["cat"] = "marche"
            else:
                div_ok = out["div"]["baissiere"] if t["sens"] == "short" else out["div"]["haussiere"]
                t["div"] = div_ok
                if (config.BB_MECHE_MIN <= t["meche"] <= config.BB_MECHE_MAX) and t["a_plat"] and div_ok:
                    t["cat"] = "probable"
                else:
                    t["cat"] = "sans"
            out["bb"] = t
            break

    # ─── Compression : largeur BB 4H vs minimum des 90 jours ────────────────
    larg = (up - lo) / mid
    fen = min(len(larg), config.COMPRESSION_JOURS * 6)
    hist = larg[-fen:]
    hist = hist[~np.isnan(hist)]
    if len(hist) > 100 and not np.isnan(larg[-1]):
        mn = float(np.min(hist))
        out["compression_ratio"] = float(larg[-1] / mn) if mn > 0 else np.nan
    else:
        out["compression_ratio"] = np.nan

    # ─── Marché fermé (bougies plates : TradFi la nuit / le week-end) ───────
    derniers = slice(-2, None)
    out["ferme"] = bool(np.all(b4["h"][derniers] == b4["l"][derniers]) or np.all(b4["v"][derniers] == 0))
    return out
