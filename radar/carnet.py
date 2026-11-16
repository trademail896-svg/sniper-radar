"""
SNIPER RADAR — 📒 Carnet des movers
===================================
Capture les tokens qui ont bougé de ±15 % sur 24 h, les suit 7 jours et donne
leur phase à chaque heure.

Impulsion mesurée du prix de départ (24 h avant la capture) à l'extrême
atteint depuis. retracement = (extrême − prix) / (extrême − départ).

Ordre d'évaluation de la phase :
  sortie (> 78,6 % ou 7 jours) → Zone de rebond (50–78,6 %) → Retracement
  (23,6–50 %) → Retournement (clôture 1H qui casse le dernier swing 3/3 formé
  entre le départ et l'extrême) → Essoufflement (pas de nouvel extrême depuis
  4 h ET MSO 4H en zone extrême du côté du move) → Pause (pas de nouvel
  extrême depuis 4 h, MSO pas extrême) → Impulsion.
"""
import numpy as np

from . import config, etat
from . import indicateurs as ind

_FICHIER = "carnet.json"
PHASES = ["Impulsion", "Pause", "Essoufflement", "Retournement", "Retracement", "Zone de rebond"]


def _index_ts(t, ts_ms):
    i = int(np.searchsorted(t, ts_ms, side="left"))
    return min(max(i, 0), len(t) - 1)


def _phase(e, b1, mso4h):
    t, h, l, c = b1["t"], b1["h"], b1["l"], b1["c"]
    i0 = _index_ts(t, e["depart_ts"])
    pump = e["sens"] == "pump"
    seg = h[i0:] if pump else l[i0:]
    if len(seg) == 0:
        return None
    k = int(np.argmax(seg)) if pump else int(np.argmin(seg))
    ix = i0 + k
    e["extreme"] = float(seg[k])
    e["extreme_ts"] = int(t[ix])
    prix = float(c[-1])
    imp = e["extreme"] - e["depart"]
    retr = (e["extreme"] - prix) / imp if imp else 0.0
    e["retr"] = float(retr)
    e["prix"] = prix
    heures_extreme = (len(c) - 1 - ix)

    if retr > config.RETR_SORTIE:
        return "SORTIE"
    if retr >= config.RETR_REBOND:
        return "Zone de rebond"
    if retr >= config.RETR_RETRACEMENT:
        return "Retracement"
    p = config.CARNET_PIVOT
    if pump:
        piv = [i for i in ind.pivots_bas(l, p, p) if i0 <= i < ix]
        if piv and prix < l[piv[-1]]:
            return "Retournement"
    else:
        piv = [i for i in ind.pivots_hauts(h, p, p) if i0 <= i < ix]
        if piv and prix > h[piv[-1]]:
            return "Retournement"
    if heures_extreme >= config.CARNET_HEURES_ESSOUFFLEMENT:
        ext = (not np.isnan(mso4h)) and (mso4h >= config.MSO_SURACHAT if pump else mso4h <= config.MSO_SURVENTE)
        return "Essoufflement" if ext else "Pause"
    return "Impulsion"


def mettre_a_jour(tokens_par_sym, maintenant, fichier=_FICHIER):
    """
    tokens_par_sym : symbol → token (pct24, b (bougies), m (mesures), ...).
    Retourne la liste des entrées actives du carnet.
    """
    carnet = etat.lire(fichier, {})

    # 1. Captures
    cands = [t for t in tokens_par_sym.values() if not np.isnan(t["pct24"])
             and abs(t["pct24"]) >= config.CARNET_SEUIL_PCT]
    hausses = sorted([t for t in cands if t["pct24"] > 0], key=lambda t: -t["pct24"])[:config.CARNET_MAX_PAR_COTE]
    baisses = sorted([t for t in cands if t["pct24"] < 0], key=lambda t: t["pct24"])[:config.CARNET_MAX_PAR_COTE]
    for t in hausses + baisses:
        sens = "pump" if t["pct24"] > 0 else "dump"
        e = carnet.get(t["symbol"])
        if e and e["sens"] == sens:
            continue
        b1 = t["b"]["1h"]
        i_dep = max(len(b1["c"]) - 25, 0)
        carnet[t["symbol"]] = {
            "symbol": t["symbol"], "base": t["base"], "sens": sens,
            "capture_ts": maintenant, "capture_pct": t["pct24"],
            "depart": float(b1["c"][i_dep]), "depart_ts": int(b1["t"][i_dep]),
            "phases": [],
        }

    # 2. Suivi
    actifs = []
    for sym in list(carnet):
        e = carnet[sym]
        age_h = (maintenant - e["capture_ts"]) / 3600.0
        t = tokens_par_sym.get(sym)
        if age_h > config.CARNET_JOURS * 24:
            del carnet[sym]
            continue
        if t is None:                       # pas de données ce run : on garde sans mettre à jour
            continue
        ph = _phase(e, t["b"]["1h"], t["m"]["mso4h"])
        if ph is None:
            continue
        if ph == "SORTIE":
            del carnet[sym]
            continue
        if not e["phases"] or e["phases"][-1]["phase"] != ph:
            e["phases"].append({"phase": ph, "ts": maintenant})
            e["phases"] = e["phases"][-20:]
        e["phase"] = ph
        e["phase_depuis_h"] = (maintenant - e["phases"][-1]["ts"]) / 3600.0
        e["move_pct"] = (e["extreme"] - e["depart"]) / e["depart"] * 100.0 if e["depart"] else 0.0
        actifs.append(e)
    etat.ecrire(fichier, carnet)
    return actifs
