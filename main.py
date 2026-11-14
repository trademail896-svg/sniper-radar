"""
SNIPER RADAR — point d'entrée (lancé chaque heure par GitHub Actions)
=====================================================================
1. Univers (perps USDT) + ticker 24 h
2. Bougies 1H / 4H en parallèle
3. Calculs par token (MSO 4H, BB 4H, RSI 1H, compression…)
4. Météo, carnet des movers, touches BB, score
5. Page site/index.html + petits JSON d'état dans data/
"""
import sys
import time
import traceback

import numpy as np

from radar import analyse, carnet, config, donnees, meteo, page, score
from radar.secteurs import Secteurs


def main():
    t0 = time.time()
    maintenant = int(time.time())
    print(f"=== {config.NOM} V{config.VERSION} ===")

    # 1. Univers ─────────────────────────────────────────────────────────────
    marches = donnees.charger_marches()
    tickers = donnees.charger_tickers()
    sect = Secteurs()
    tous, univers = [], []
    for m in marches:
        tk = tickers.get(m["symbol"])
        if not tk or m["base"].upper() in config.EXCLUS:
            continue
        tradfi = sect.est_tradfi(m["base"])
        jours = (maintenant * 1000 - m["launch_ms"]) / 86_400_000 if m["launch_ms"] else 9999
        t = {**m, **tk, "tradfi": tradfi, "secteur": sect.secteur(m["base"]),
             "nouveau": jours < config.JOURS_NOUVEAU, "jours": int(max(jours, 0))}
        tous.append(t)
        if tradfi or tk["qv24"] >= config.VOLUME_MIN_CRYPTO_USD:
            univers.append(t)
    print(f"[univers] {len(marches)} perps · {len(univers)} retenus "
          f"({sum(not t['tradfi'] for t in univers)} crypto ≥ {config.VOLUME_MIN_CRYPTO_USD / 1e6:.0f} M$, "
          f"{sum(t['tradfi'] for t in univers)} TradFi)")

    # 2. Bougies ─────────────────────────────────────────────────────────────
    bougies = donnees.charger_bougies([t["symbol"] for t in univers])

    # 3. Calculs par token ───────────────────────────────────────────────────
    ok = []
    for t in univers:
        b = bougies.get(t["symbol"])
        if not b:
            continue
        try:
            t["b"] = b
            t["m"] = analyse.analyser(b)
            ok.append(t)
        except Exception as ex:
            print(f"[analyse] {t['symbol']} : {ex}")
    # Date de lancement absente (Bitget) : âge = historique de bougies 4H disponible
    for t in ok:
        if not t["launch_ms"]:
            n4 = len(t["b"]["4h"]["t"])
            if n4 < config.NB_BOUGIES_4H * 0.85:          # historique plus court que ce qu'on demande
                jours = (maintenant * 1000 - int(t["b"]["4h"]["t"][0])) / 86_400_000
                t["jours"] = int(max(jours, 0))
                t["nouveau"] = jours < config.JOURS_NOUVEAU
    par_sym = {t["symbol"]: t for t in ok}
    crypto = [t for t in ok if not t["tradfi"]]
    print(f"[analyse] {len(ok)} tokens analysés")
    if not ok:
        print("Aucune donnée : arrêt sans toucher à la page.")
        return 2

    # 4. Météo ───────────────────────────────────────────────────────────────
    me = meteo.calculer(crypto, maintenant)
    btc = next((t for t in ok if t["base"] == "BTC"), None)
    regime = meteo.regime_btc(btc)

    # 5. Carnet + touches BB ─────────────────────────────────────────────────
    entrees = carnet.mettre_a_jour(par_sym, maintenant)
    touches = [t for t in ok if t["m"]["bb"]]

    cand = {e["symbol"] for e in entrees} | {t["symbol"] for t in touches}
    oi24 = donnees.variation_oi_24h(sorted(cand)) if cand else {}

    movers = []
    for e in entrees:
        t = par_sym.get(e["symbol"])
        if not t:
            continue
        sens = score.sens_mover(e)
        s = score.noter(sens, e["phase"] in ("Retournement", "Zone de rebond"), t, me, oi24.get(e["symbol"]))
        movers.append({"e": e, "token": t, "score": s})
    movers.sort(key=lambda x: score.cle_tri(x["score"], x["e"]["phase_depuis_h"], x["token"]["qv24"]))

    bb = {"probable": [], "sans": [], "marche": []}
    for t in touches:
        tb = t["m"]["bb"]
        s = score.noter(tb["sens"], tb["cat"] == "probable", t, me, oi24.get(t["symbol"]), tb["cat"] == "marche")
        bb[tb["cat"]].append({"token": t, "bb": tb, "score": s})
    for k in bb:
        bb[k].sort(key=lambda x: score.cle_tri(x["score"], x["bb"]["bougies_depuis"] * 4, x["token"]["qv24"]))

    # 6. Compression, nouveaux, rotation ─────────────────────────────────────
    comp = [{"token": t, "ratio": t["m"]["compression_ratio"]} for t in ok
            if not np.isnan(t["m"]["compression_ratio"]) and t["m"]["compression_ratio"] <= config.COMPRESSION_TOLERANCE
            and not t["m"]["ferme"]]
    comp.sort(key=lambda c: c["ratio"])
    comp = comp[:config.COMPRESSION_MAX_AFFICHES]

    nouveaux = sorted([t for t in ok if t["nouveau"]], key=lambda t: t["jours"])

    groupes = {}
    for t in ok:
        if np.isnan(t["pct24"]):
            continue
        groupes.setdefault(t["secteur"], {"vals": [], "tradfi": t["tradfi"]})["vals"].append(t["pct24"])
    rotation = [{"nom": n, "pct": float(np.mean(g["vals"])), "nb": len(g["vals"]), "tradfi": g["tradfi"]}
                for n, g in groupes.items() if len(g["vals"]) >= (1 if g["tradfi"] else 3)]
    rotation.sort(key=lambda s: (s["nom"] == "Non classé", -s["pct"]))
    compte = {}
    for t in ok:
        compte[t["secteur"]] = compte.get(t["secteur"], 0) + 1
    secteurs_filtres = [s for s, _ in sorted(compte.items(), key=lambda kv: -kv[1]) if s != "Non classé"] + \
                       (["Non classé"] if "Non classé" in compte else [])

    tradfi = sorted([t for t in ok if t["tradfi"]], key=lambda t: (t["secteur"], t["base"]))

    # 7. Page ────────────────────────────────────────────────────────────────
    chemin = page.generer({
        "maintenant": maintenant, "meteo": me, "regime_btc": regime, "movers": movers, "bb": bb,
        "compression": comp, "nouveaux": nouveaux, "rotation": rotation, "secteurs_filtres": secteurs_filtres,
        "tradfi": tradfi, "nb_crypto": len(crypto), "nb_tradfi": len(tradfi), "nb_ok": len(ok),
        "duree": time.time() - t0,
    })
    print(f"[page] {chemin} · {len(movers)} movers · BB {sum(len(v) for v in bb.values())} · "
          f"compression {len(comp)} · nouveaux {len(nouveaux)} · {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(3)
