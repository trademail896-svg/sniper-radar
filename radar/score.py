"""
SNIPER RADAR — Score de confirmations (tri des listes)
=====================================================
Score V2 (21-11-2026) — un point par confirmation, 4 au maximum :
 1. Setup actif (BB 4H « Retournement probable », ou mover en Retournement /
    Zone de rebond)
 2. Momentum : mover en tendance (Impulsion, Retracement, Zone de rebond) avec
    MSO 4H extrême DANS le sens du trade (≥ 85 long / ≤ 15 short)
 3. Divergence RSI 1H confirmée dans le sens du setup
 4. Dans le sens de la météo (long : % verts ≥ 50 et qui monte sur 4 h ;
    short : l'inverse)
Pénalité : « marche sur la bande » seulement.
Retirés (feuille de match 14 j, 2589 signaux, 24 h net de frais) :
 - MSO à contre-sens (survente pour un long) : −2,76 % avec / +1,18 % sans
 - Foule (funding / OI) : −2,41 % avec / −0,94 % sans → affichée en info, 0 point
 - Pénalité MSO extrême dans le sens du trade : faisait MIEUX que sans → devenue
   le point momentum pour les movers en tendance
L'ancien score (V1, /5) est encore calculé et suivi dans la feuille de match
pour comparer les deux pendant quelques semaines.
Égalité : setup le plus récent, puis le plus liquide.
"""
import numpy as np

from . import config


def sens_mover(e):
    pump = e["sens"] == "pump"
    if e["phase"] in ("Essoufflement", "Retournement", "Pause"):
        return "short" if pump else "long"
    return "long" if pump else "short"          # Impulsion, Retracement, Zone de rebond


PHASES_TENDANCE = ("Impulsion", "Retracement", "Zone de rebond")


def noter(sens, setup_actif, token, meteo, oi24, marche_bande=False, tendance=False):
    """Score V2 (voir l'en-tête). Garde l'ancien score dans « v1 »."""
    v1 = noter_v1(sens, setup_actif, token, meteo, oi24, marche_bande)
    m = token["m"]
    mso = m["mso4h"]
    r1 = v1["raisons"]
    raisons = [x for x in r1 if x in ("setup", "divergence", "météo")]
    momentum = tendance and not np.isnan(mso) and ((sens == "long" and mso >= config.MSO_SURACHAT)
                                                  or (sens == "short" and mso <= config.MSO_SURVENTE))
    if momentum:
        raisons.insert(1 if "setup" in raisons else 0, "momentum")
    infos = ["foule"] if "foule" in r1 else []
    return {"points": len(raisons), "raisons": raisons, "infos": infos, "penalite": bool(marche_bande),
            "sens": sens, "v1": {"points": v1["points"], "penalite": v1["penalite"]}}


def noter_v1(sens, setup_actif, token, meteo, oi24, marche_bande=False):
    """Ancien score /5 (MSO à contre-sens, foule), gardé pour la comparaison."""
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
