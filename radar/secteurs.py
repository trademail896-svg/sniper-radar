"""
SNIPER RADAR — Secteurs
=======================
data/secteurs.json = {"manuel": {BASE: secteur}, "auto": {BASE: secteur}}
- "manuel" : les corrections de Dave (toujours prioritaires, même sur la liste TradFi)
- "auto"   : rempli par tools/remplir_secteurs.py (catégories CoinGecko)
Les contrats TradFi prennent leur secteur dans config.TRADFI.
"""
import re

from . import config, etat


def base_simple(base):
    """1000PEPE → PEPE, 10000SATS → SATS, SHIB1000 → SHIB."""
    b = base.upper()
    b = re.sub(r"^1[0]{2,}", "", b)
    b = re.sub(r"1[0]{2,}$", "", b)
    return b or base.upper()


SECTEURS_TRADFI = {"Actions US", "Indices", "Métaux", "Énergie"}


class Secteurs:
    def __init__(self):
        d = etat.lire("secteurs.json", {"manuel": {}, "auto": {}})
        self.manuel = {k.upper(): v for k, v in (d.get("manuel") or {}).items()}
        self.auto = {k.upper(): v for k, v in (d.get("auto") or {}).items()}

    def est_tradfi(self, base):
        return self.secteur(base) in SECTEURS_TRADFI

    def secteur(self, base):
        b = base_simple(base)
        m = self.manuel.get(base.upper()) or self.manuel.get(b)
        if m:
            return m
        if b in config.TRADFI:
            return config.TRADFI[b]
        return self.auto.get(b) or "Non classé"
