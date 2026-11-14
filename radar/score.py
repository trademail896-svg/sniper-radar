"""
SNIPER RADAR — Score de confirmations (tri des listes)
=====================================================
Un point par confirmation, 5 au maximum :
 1. Setup actif (BB 4H « Retournement probable », ou mover en Retournement /
    Zone de rebond)
 2. MSO 4H du bon côté (survente pour un long, surachat pour un short)
 3. Divergence RSI 1H confirmée dans le sens du setup
 4. Dans le sens de la météo (long : % verts ≥ 50 et qui monte sur 4 h ;
    short : l'inverse)
 5. Foule du mauvais bord (funding ≥ +0,03 % pour un short / ≤ −0,03 % pour un
    long, OU OI +5 % sur 24 h pendant que le prix va contre le setup)
Pénalité : MSO 4H extrême dans le sens du trade, ou « marche sur la bande ».
Égalité : setup le plus récent, puis le plus liquide.
"""
import numpy as np

from . import config


def sens_mover(e):
    pump = e["sens"] == "pump"
    if e["phase"] in ("Essoufflement", "Retournement", "Pause"):
        return "short" if pump else "long"
    return "long" if pump else "short"          # Impulsion, Retracement, Zone de rebond


def noter(sens, setup_actif, token, meteo, oi24, marche_bande=False):
    m = token["m"]
    mso = m["mso4h"]
    raisons = []
    pts = 0
    if setup_actif:
        pts += 1
        raisons.append("setup")
    if not np.isnan(mso) and ((sens == "long" and mso <= config.MSO_SURVENTE)
                              or (sens == "short" and mso >= config.MSO_SURACHAT)):
        pts += 1
        raisons.append("MSO")
    if (sens == "long" and m["div"]["haussiere"]) or (sens == "short" and m["div"]["baissiere"]):
        pts += 1
        raisons.append("divergence")
    v, d4 = meteo.get("verts"), meteo.get("verts_d4")
    if v is not None:
        monte = d4 is None or d4 > 0
        baisse = d4 is None or d4 < 0
        if (sens == "long" and v >= 50 and monte) or (sens == "short" and v < 50 and baisse):
            pts += 1
            raisons.append("météo")
    f = token["funding"]
    pct = token["pct24"]
    foule = False
    if not np.isnan(f):
        foule = (sens == "short" and f >= config.FUNDING_FOULE) or (sens == "long" and f <= -config.FUNDING_FOULE)
    if not foule and oi24 is not None and not np.isnan(oi24) and oi24 >= config.OI_FOULE_PCT and not np.isnan(pct):
        foule = (sens == "short" and pct > 0) or (sens == "long" and pct < 0)
    if foule:
        pts += 1
        raisons.append("foule")
    penalite = marche_bande or (not np.isnan(mso) and ((sens == "long" and mso >= config.MSO_SURACHAT)
                                                       or (sens == "short" and mso <= config.MSO_SURVENTE)))
    return {"points": pts, "raisons": raisons, "penalite": bool(penalite), "sens": sens}


def cle_tri(score, age_h, volume):
    return (score["penalite"], -score["points"], age_h, -volume)
