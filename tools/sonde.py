"""Diagnostic : contrats disponibles sur BloFin DEMO vs watchlist TradingView « blofindemo »."""
import requests
WATCH = "1000BONK 1000FLOKI AAVE ADA AERO ALGO APE APT ARB AR ASTER ATOM AVAX AXL BCH BNB BRETT BTC CAKE CC CRV DASH DOGE DOT ENA ETC ETHFI ETH FARTCOIN FET FIL HBAR HYPE ICP INJ JASMY JUP KAS LDO LINK LTC LUNA2 MNT MON M NEAR NOT ONDO OP PENDLE PENGU PEOPLE PEPE PIPPIN POL POPCAT PUMP QNT RENDER SEI SHIB SOL SPX STRK STX SUI TAO TIA TRUMP TRX TURBO UNI VIRTUAL WIF WLD WLFI XAUT XLM XMR XPL XRP ZEC ZEN ZK".split()
for nom, url in (("DEMO", "https://demo-trading-openapi.blofin.com/api/v1/market/instruments"),
                 ("LIVE", "https://openapi.blofin.com/api/v1/market/instruments")):
    try:
        d = requests.get(url, timeout=30).json().get("data", [])
    except Exception as e:
        print(nom, "ERREUR", e); continue
    usdt = sorted(x["instId"].replace("-USDT", "") for x in d if x.get("instId", "").endswith("-USDT")
                  and str(x.get("state", "live")).lower() == "live")
    print(f"{nom}_NB {len(usdt)}")
    if nom == "DEMO":
        demo = set(usdt)
        print("DEMO_LISTE", " ".join(usdt))
        print("A_RETIRER (dans la watchlist, absents de la démo):", " ".join(sorted(set(WATCH) - demo)) or "aucun")
        print("A_AJOUTER (dans la démo, absents de la watchlist):", " ".join(sorted(demo - set(WATCH))) or "aucun")
