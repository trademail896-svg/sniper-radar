# 🎯 SNIPER RADAR

Dashboard web rafraîchi chaque heure : météo du marché, rotation des secteurs,
carnet des movers, touches BB 4H, compression, nouveaux contrats et TradFi.
Données Bitget (perps USDT), OI 24 h via OKX, publiques, sans clé API.

Page : **https://trademail896-svg.github.io/sniper-radar/**

## Installation (une seule fois)

1. **Créer le dépôt** : GitHub → *New repository* → nom `sniper-radar` → **Public** → *Create*.
2. **Mettre les fichiers** : *uploading an existing file* → glisser TOUT le contenu du dossier
   (y compris le dossier `.github`) → *Commit changes*.
3. **Activer la page** : *Settings → Pages → Source* : **GitHub Actions**.
4. **Permettre au scan d'écrire** : *Settings → Actions → General → Workflow permissions* :
   **Read and write permissions** → *Save*.
5. **Classer les secteurs** : onglet *Actions* → « SNIPER RADAR — remplir les secteurs » →
   *Run workflow*. (Facultatif : une clé CoinGecko « Demo » gratuite dans
   *Settings → Secrets and variables → Actions* sous le nom `COINGECKO_API_KEY` rend ça plus rapide.)
6. **Premier scan** : onglet *Actions* → « SNIPER RADAR — scan horaire » → *Run workflow*.
   Ensuite il roule tout seul à 7 min après chaque heure.

La direction de la météo (▲▼ sur 4 h et 24 h) apparaît après 4 h et 24 h de scans.

## Corriger un secteur

Dans `data/secteurs.json`, partie `"manuel"` (prioritaire sur tout le reste) :

```json
"manuel": { "HYPE": "L1", "ZEC": "Confidentialité" }
```

Un contrat TradFi manquant : ajoute sa base dans `TRADFI` de `radar/config.py`.

## Réglages

Tout est dans `radar/config.py` (volume minimum, seuils du carnet, BB, MSO 85/15,
funding, etc.).

## Fichiers

| Fichier | Rôle |
|---|---|
| `main.py` | enchaîne tout, chaque heure |
| `radar/donnees.py` | collecte Bitget + OKX (CCXT) |
| `radar/indicateurs.py` | EMA, BB, RSI, pivots, Heikin Ashi, MSO LuxAlgo (validés contre TradingView) |
| `radar/analyse.py` | calculs par token |
| `radar/meteo.py` | météo du marché |
| `radar/carnet.py` | carnet des movers et phases |
| `radar/score.py` | score de confirmations /5 |
| `radar/page.py` | page HTML |
| `data/*.json` | mémoire entre les scans (carnet, météo, secteurs) |
