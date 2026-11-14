"""
SNIPER RADAR — Remplit data/secteurs.json (partie « auto ») avec CoinGecko
=========================================================================
Pour chaque secteur, lit les coins de la catégorie CoinGecko (par capitalisation,
1000 premiers). Un symbole prend le premier secteur trouvé dans l'ordre de
PRIORITE. La partie « manuel » (tes corrections) n'est jamais modifiée.

Clé facultative : secret GitHub COINGECKO_API_KEY (clé « Demo » gratuite).
Sans clé, l'API publique marche mais plus lentement.
"""
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from radar import config, etat  # noqa: E402

# Ordre = priorité (un meme coin qui est aussi un L1 reste « Memes »)
PRIORITE = [
    ("meme-token", "Memes"),
    ("artificial-intelligence", "IA"),
    ("real-world-assets-rwa", "RWA"),
    ("gaming", "Gaming"),
    ("privacy-coins", "Confidentialité"),
    ("layer-2", "L2"),
    ("decentralized-finance-defi", "DeFi"),
    ("layer-1", "L1"),
]
PAGES = 4


def lire_categorie(cat, cle):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    entetes = {"x-cg-demo-api-key": cle} if cle else {}
    syms = []
    for page in range(1, PAGES + 1):
        for essai in range(4):
            r = requests.get(url, params={"vs_currency": "usd", "category": cat, "order": "market_cap_desc",
                                          "per_page": 250, "page": page}, headers=entetes, timeout=30)
            if r.status_code == 429:
                time.sleep(20 * (essai + 1))
                continue
            r.raise_for_status()
            break
        else:
            print(f"  {cat} p{page} : limite atteinte, on passe")
            break
        data = r.json()
        syms += [d["symbol"].upper() for d in data if d.get("symbol")]
        time.sleep(2.5 if cle else 7)
        if len(data) < 250:
            break
    return syms


def main():
    cle = os.getenv("COINGECKO_API_KEY", "").strip()
    d = etat.lire("secteurs.json", {"manuel": {}, "auto": {}})
    auto = {}
    for cat, nom in PRIORITE:
        syms = lire_categorie(cat, cle)
        ajout = 0
        for s in syms:
            if s not in auto and s not in config.TRADFI:
                auto[s] = nom
                ajout += 1
        print(f"{nom:16} {len(syms):5} coins lus · {ajout} ajoutés")
    d["auto"] = auto
    d.setdefault("manuel", {})
    etat.ecrire("secteurs.json", d)
    print(f"Total auto : {len(auto)} · manuel : {len(d['manuel'])}")


if __name__ == "__main__":
    main()
