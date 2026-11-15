"""
SNIPER RADAR — Journal et feuille de match
==========================================
1. Enregistre chaque token mis en avant (carnet, touches BB 4H) avec son score,
   son sens et son prix. Une seule entrée par token / liste / sens sur 12 h.
2. Mesure ce que le prix a fait 4 h, 24 h et 72 h après, DANS LE SENS du setup :
   résultat à l'échéance, meilleur moment (MFE) et pire moment (MAE).
3. Compare au reste du marché : même fenêtre, même sens, médiane de tous les
   tokens scannés → « avance » = résultat − médiane du marché.
4. Feuille de match (14 derniers jours) par score, par liste, par phase,
   + les plus gros mouvements des dernières 24 h que le radar n'a pas mis en avant.
Résultats bruts, sans frais (≈ 0,12 % aller-retour à retrancher).
"""
import numpy as np

from . import etat

_FICHIER = "journal.json"
HORIZONS = (4, 24, 72)
DEDOUBLON_H = 12
GARDER_JOURS = 21
FEUILLE_JOURS = 14


def _cle(e):
    return f'{e["symbol"]}|{e["liste"]}|{e["sens"]}'


def enregistrer(journal, maintenant, movers, bb):
    recents = {}
    for e in journal:
        if maintenant - e["ts"] < DEDOUBLON_H * 3600:
            recents[_cle(e)] = True
    nouveaux = []

    def ajout(t, liste, detail, s):
        e = {"ts": maintenant, "symbol": t["symbol"], "base": t["base"], "liste": liste, "detail": detail,
             "score": s["points"], "penalite": s["penalite"], "raisons": s["raisons"], "sens": s["sens"],
             "prix": float(t["last"]) if not np.isnan(t["last"]) else float(t["b"]["1h"]["c"][-1]),
             "tradfi": t["tradfi"], "secteur": t["secteur"], "eval": {}}
        if _cle(e) not in recents:
            recents[_cle(e)] = True
            nouveaux.append(e)

    for mv in movers:
        ajout(mv["token"], "carnet", mv["e"]["phase"], mv["score"])
    for cat, items in bb.items():
        for it in items:
            ajout(it["token"], f"bb_{cat}", it["bb"]["cote"], it["score"])
    journal.extend(nouveaux)
    return len(nouveaux)


def _prix_a(b1, ts_ms):
    """Clôture de la dernière bougie 1H fermée à ts_ms (ou avant)."""
    t = b1["t"]
    i = int(np.searchsorted(t, ts_ms - 3_600_000, side="right")) - 1
    return (float(b1["c"][i]), i) if 0 <= i < len(t) else (np.nan, -1)


def _rendement_marche(par_sym, ts0, ts1, sens):
    vals = []
    for t in par_sym.values():
        b1 = t["b"]["1h"]
        p0, _ = _prix_a(b1, ts0 * 1000)
        p1, _ = _prix_a(b1, ts1 * 1000)
        if p0 and p1 and not np.isnan(p0) and not np.isnan(p1):
            r = (p1 - p0) / p0 * 100.0
            vals.append(r if sens == "long" else -r)
    return float(np.median(vals)) if vals else np.nan


def evaluer(journal, par_sym, maintenant):
    cache = {}
    nb = 0
    for e in journal:
        for h in HORIZONS:
            k = str(h)
            if k in e["eval"] or maintenant < e["ts"] + h * 3600:
                continue
            t = par_sym.get(e["symbol"])
            if t is None:
                if maintenant > e["ts"] + (h + 12) * 3600:
                    e["eval"][k] = None
                continue
            b1 = t["b"]["1h"]
            fin = e["ts"] + h * 3600
            p1, i1 = _prix_a(b1, fin * 1000)
            i0 = int(np.searchsorted(b1["t"], e["ts"] * 1000, side="left"))
            if np.isnan(p1) or i1 < i0:
                continue
            hh = float(np.max(b1["h"][i0:i1 + 1]))
            ll = float(np.min(b1["l"][i0:i1 + 1]))
            p0 = e["prix"]
            sgn = 1.0 if e["sens"] == "long" else -1.0
            ret = sgn * (p1 - p0) / p0 * 100.0
            mfe = ((hh - p0) if sgn > 0 else (p0 - ll)) / p0 * 100.0
            mae = ((ll - p0) if sgn > 0 else (p0 - hh)) / p0 * 100.0
            ck = (e["ts"] // 3600, h, e["sens"])
            if ck not in cache:
                cache[ck] = _rendement_marche(par_sym, e["ts"], fin, e["sens"])
            bench = cache[ck]
            e["eval"][k] = {"ret": ret, "mfe": mfe, "mae": mae, "marche": bench,
                            "avance": ret - bench if not np.isnan(bench) else None}
            nb += 1
    return nb


def _stats(entrees, h="24"):
    ev = [e["eval"][h] for e in entrees if e["eval"].get(h)]
    if not ev:
        return None
    rets = [x["ret"] for x in ev]
    av = [x["avance"] for x in ev if x["avance"] is not None]
    return {"n": len(ev), "moy": float(np.mean(rets)), "gagnants": 100.0 * sum(r > 0 for r in rets) / len(rets),
            "avance": float(np.mean(av)) if av else None,
            "mfe": float(np.mean([x["mfe"] for x in ev])), "mae": float(np.mean([x["mae"] for x in ev]))}


def feuille(journal, maintenant, ok):
    fen = [e for e in journal if maintenant - e["ts"] <= FEUILLE_JOURS * 86400]
    res = {"jours": FEUILLE_JOURS, "nb_signaux": len(fen), "horizons": {}}
    for h in ("4", "24", "72"):
        par_score = {}
        for s in range(6):
            st = _stats([e for e in fen if e["score"] == s and not e["penalite"]], h)
            if st:
                par_score[str(s)] = st
        pen = _stats([e for e in fen if e["penalite"]], h)
        par_liste = {}
        for li in sorted({e["liste"] for e in fen}):
            st = _stats([e for e in fen if e["liste"] == li], h)
            if st:
                par_liste[li] = st
        par_phase = {}
        for ph in sorted({e["detail"] for e in fen if e["liste"] == "carnet"}):
            st = _stats([e for e in fen if e["liste"] == "carnet" and e["detail"] == ph], h)
            if st:
                par_phase[ph] = st
        haut = _stats([e for e in fen if e["score"] >= 4 and not e["penalite"]], h)
        bas = _stats([e for e in fen if e["score"] <= 1 or e["penalite"]], h)
        res["horizons"][h] = {"par_score": par_score, "penalite": pen, "par_liste": par_liste,
                              "par_phase": par_phase, "haut": haut, "bas": bas}
    # Coups ratés : plus gros mouvements 24 h absents des mises en avant des dernières 24 h
    vus = {}
    for e in journal:
        if maintenant - e["ts"] <= 86400:
            vus.setdefault(e["symbol"], set()).add(e["sens"])
    rates = []
    for t in ok:
        p = t["pct24"]
        if np.isnan(p):
            continue
        sens = "long" if p > 0 else "short"
        if sens not in vus.get(t["symbol"], set()):
            rates.append({"base": t["base"], "symbol": t["symbol"], "pct24": float(p), "sens": sens,
                          "secteur": t["secteur"], "mso4h": t["m"]["mso4h"]})
    rates.sort(key=lambda r: -abs(r["pct24"]))
    res["rates"] = rates[:5]
    return res


def mettre_a_jour(maintenant, movers, bb, par_sym, ok):
    journal = etat.lire(_FICHIER, [])
    journal = [e for e in journal if maintenant - e["ts"] <= GARDER_JOURS * 86400]
    nb_ev = evaluer(journal, par_sym, maintenant)
    nb_new = enregistrer(journal, maintenant, movers, bb)
    etat.ecrire(_FICHIER, journal)
    f = feuille(journal, maintenant, ok)
    f["maj"] = maintenant
    etat.ecrire("feuille.json", f)
    print(f"[journal] {nb_new} nouveaux signaux · {nb_ev} évaluations · {len(journal)} au total")
    return f
