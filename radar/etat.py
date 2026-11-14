"""SNIPER RADAR — Lecture / écriture des petits fichiers JSON d'état."""
import json
import math
import os

from . import config


def _chemin(nom):
    return os.path.join(config.DOSSIER_DATA, nom)


def lire(nom, defaut):
    try:
        with open(_chemin(nom), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return defaut


def _propre(x):
    if isinstance(x, float):
        return None if (math.isnan(x) or math.isinf(x)) else round(x, 8)
    if isinstance(x, dict):
        return {k: _propre(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_propre(v) for v in x]
    if hasattr(x, "item"):
        return _propre(x.item())
    return x


def ecrire(nom, data):
    os.makedirs(config.DOSSIER_DATA, exist_ok=True)
    tmp = _chemin(nom) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_propre(data), f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, _chemin(nom))
