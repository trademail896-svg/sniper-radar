"""
SNIPER RADAR — 🌡️ Météo du marché (crypto seulement)
====================================================
% verts 24 h, % au-dessus de l'EMA50 4H, leur direction (vs il y a 4 h et
24 h), régime BTC 4H, funding moyen, OI total et sa variation sur 24 h.
"""
import numpy as np

from . import config, etat

_FICHIER = "meteo_historique.json"


def _valeur_il_y_a(hist, maintenant, heures, cle):
    cible = maintenant - heures * 3600
    meilleurs = [h for h in hist if abs(h["ts"] - cible) <= 45 * 60 and h.get(cle) is not None]
    if not meilleurs:
        return None
    return min(meilleurs, key=lambda h: abs(h["ts"] - cible))[cle]


def calculer(tokens, maintenant):
    """tokens = liste de dicts crypto (pct24, funding, oi_valeur, mesures)."""
    pcts = [t["pct24"] for t in tokens if not np.isnan(t["pct24"])]
    au_dessus = [t["m"]["close_4h"] > t["m"]["ema50_4h"] for t in tokens
                 if not np.isnan(t["m"]["ema50_4h"])]
    fund = [t["funding"] for t in tokens if not np.isnan(t["funding"])]
    m = {
        "ts": maintenant,
        "verts": 100.0 * sum(p > 0 for p in pcts) / len(pcts) if pcts else None,
        "ema50": 100.0 * sum(au_dessus) / len(au_dessus) if au_dessus else None,
        "funding_moy": float(np.mean(fund)) if fund else None,
        "oi_total": float(sum(t["oi_valeur"] for t in tokens)),
        "nb": len(tokens),
    }
    hist = etat.lire(_FICHIER, [])
    hist = [h for h in hist if h["ts"] >= maintenant - config.METEO_HISTORIQUE_HEURES * 3600 and h["ts"] != maintenant]
    for cle in ("verts", "ema50"):
        for hrs in (4, 24):
            v = _valeur_il_y_a(hist, maintenant, hrs, cle)
            m[f"{cle}_d{hrs}"] = (m[cle] - v) if (v is not None and m[cle] is not None) else None
    oi24 = _valeur_il_y_a(hist, maintenant, 24, "oi_total")
    m["oi_d24_pct"] = ((m["oi_total"] - oi24) / oi24 * 100.0) if oi24 else None
    hist.append({k: m[k] for k in ("ts", "verts", "ema50", "funding_moy", "oi_total")})
    etat.ecrire(_FICHIER, hist)
    m["historique_verts"] = [h["verts"] for h in hist[-48:]]
    m["historique_ema50"] = [h["ema50"] for h in hist[-48:]]
    return m


def regime_btc(btc):
    """btc = token BTC (mesures). Haussier / Baissier / Neutre."""
    if btc is None:
        return "Inconnu", ""
    mm = btc["m"]
    c, e, p = mm["close_4h"], mm["ema50_4h"], mm["ema50_pente"]
    if np.isnan(e) or np.isnan(p):
        return "Inconnu", ""
    ecart = (c - e) / e * 100.0
    ecart_txt = f"{ecart:+.1f}".replace(".", ",").replace("-", "−")
    if c > e and p > 0:
        return "Haussier", f"Prix {ecart_txt} % vs EMA50 4H, EMA50 qui monte"
    if c < e and p < 0:
        return "Baissier", f"Prix {ecart_txt} % vs EMA50 4H, EMA50 qui baisse"
    return "Neutre", f"Prix {ecart_txt} % vs EMA50 4H, pente pas d'accord"
