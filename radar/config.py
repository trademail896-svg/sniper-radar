"""
SNIPER RADAR — Réglages
=======================
Tous les réglages de la spec étape 1 (validée par Dave le 14-11-2026).
Changer une valeur ici suffit : aucun autre fichier n'a de chiffre en dur.
"""
import os

VERSION = "1.00"
NOM = "SNIPER RADAR"

# ─── Dossiers ────────────────────────────────────────────────────────────────
DOSSIER_DATA = os.getenv("RADAR_DATA", "data")
DOSSIER_SITE = os.getenv("RADAR_SITE", "site")
FUSEAU = "America/Toronto"

# ─── Plateformes ─────────────────────────────────────────────────────────────
# Bybit bloque les serveurs de GitHub (États-Unis) → Bitget pour tout,
# OKX seulement pour l'historique d'open interest des candidats.
PLATEFORME = "bitget"
PLATEFORME_OI = "okx"
RATE_LIMIT_MS = 250                  # pause min entre 2 requêtes, par connexion

# ─── Univers ─────────────────────────────────────────────────────────────────
VOLUME_MIN_CRYPTO_USD = 3_000_000       # volume 24 h minimum (crypto seulement) — 3 M$ ≈ 110 cryptos sur Bitget
JOURS_NOUVEAU = 14                      # badge 🆕 : contrat lancé (ou 1re bougie 4H) depuis moins de N jours
EXCLUS = {"USDC", "USDT", "BUSD", "DAI", "FDUSD", "TUSD", "PYUSD", "USDE", "USDS", "BTCDOM"}

# TradFi : base du contrat → secteur. Ajoute une ligne ici si la plateforme lance un nouveau contrat.
# Un token crypto classé ici par erreur se corrige dans data/secteurs.json (« manuel »).
TRADFI = {
    # Métaux
    "XAU": "Métaux", "XAG": "Métaux", "XPT": "Métaux", "XPD": "Métaux",
    "PAXG": "Métaux", "XAUT": "Métaux", "GOLD": "Métaux", "SILVER": "Métaux", "COPPER": "Métaux",
    # Énergie
    "CL": "Énergie", "WTI": "Énergie", "BRENT": "Énergie", "OIL": "Énergie",
    "USOIL": "Énergie", "UKOIL": "Énergie", "NATGAS": "Énergie", "NG": "Énergie",
    # Indices
    "SPX": "Indices", "SPY": "Indices", "QQQ": "Indices", "NDX": "Indices",
    "NAS100": "Indices", "US30": "Indices", "US500": "Indices", "DJI": "Indices",
    # Actions US
    "TSLA": "Actions US", "NVDA": "Actions US", "AAPL": "Actions US", "MSFT": "Actions US",
    "AMZN": "Actions US", "GOOGL": "Actions US", "GOOG": "Actions US", "META": "Actions US",
    "NFLX": "Actions US", "AMD": "Actions US", "INTC": "Actions US", "COIN": "Actions US",
    "MSTR": "Actions US", "HOOD": "Actions US", "CRCL": "Actions US", "PLTR": "Actions US",
    "MRVL": "Actions US", "MU": "Actions US", "AVGO": "Actions US", "ORCL": "Actions US",
    "BABA": "Actions US", "CRWV": "Actions US",
}

# ─── Bougies ─────────────────────────────────────────────────────────────────
NB_BOUGIES_1H = 300
NB_BOUGIES_4H = 600
MIN_BOUGIES = 20                     # un contrat tout neuf est quand même analysé
WORKERS = 4

# ─── Indicateurs ─────────────────────────────────────────────────────────────
EMA_LONGUEUR = 50
BB_LONGUEUR = 20
BB_MULT = 2.0
RSI_LONGUEUR = 14
DIV_PIVOT_GAUCHE = 5
DIV_PIVOT_DROITE = 5
DIV_FENETRE_1H = 48

# MSO (Market Structure Oscillator LuxAlgo) — réglages de Dave
MSO_POIDS = (1.0, 3.0, 2.0)          # court, intermédiaire, long terme
MSO_LISSAGE = 1                      # Dave : doit rester à 1
MSO_SURACHAT = 85.0
MSO_SURVENTE = 15.0
MSO_SUR_HEIKIN_ASHI = True           # comme le LuxAlgo sur le chart HA de Dave

# ─── Météo ───────────────────────────────────────────────────────────────────
BTC_PENTE_BOUGIES = 3                # EMA50 4H « qui monte » = plus haute qu'il y a 3 bougies 4H
METEO_HISTORIQUE_HEURES = 24 * 30

# ─── Carnet des movers ───────────────────────────────────────────────────────
CARNET_SEUIL_PCT = 15.0
CARNET_MAX_PAR_COTE = 10
CARNET_JOURS = 7
CARNET_PIVOT = 3                     # swing 1H : pivot 3/3
CARNET_HEURES_ESSOUFFLEMENT = 4
RETR_SORTIE = 0.786
RETR_REBOND = 0.50
RETR_RETRACEMENT = 0.236

# ─── BB 4H ───────────────────────────────────────────────────────────────────
BB_MECHE_MIN = 0.5                   # % hors de la bande
BB_MECHE_MAX = 2.0
BB_MECHE_TENDANCE = 5.0
BB_PENTE_MAX_PCT = 3.0               # moyenne « à plat » : pente ≤ 3 % sur 24 h
BB_PENTE_BOUGIES = 6                 # 24 h = 6 bougies 4H
BB_TOUCHE_BOUGIES = 6                # une touche reste affichée 6 bougies 4H

# ─── Compression ─────────────────────────────────────────────────────────────
COMPRESSION_JOURS = 90
COMPRESSION_TOLERANCE = 1.05         # largeur ≤ 105 % du minimum des 90 jours
COMPRESSION_MAX_AFFICHES = 15

# ─── Score ───────────────────────────────────────────────────────────────────
FUNDING_FOULE = 0.0003               # 0,03 %
OI_FOULE_PCT = 5.0

# ─── Page ────────────────────────────────────────────────────────────────────
PAGE_RECHARGE_SEC = 600
TV_PREFIXE = "BITGET"
