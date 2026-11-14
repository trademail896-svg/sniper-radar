"""
SNIPER RADAR — Page HTML (dark mode 2026)
=========================================
Génère site/index.html : une seule page autonome (CSS + petit JS de filtres).
"""
import html
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np

from . import config

TZ = ZoneInfo(config.FUSEAU)

PHASE_COUL = {
    "Impulsion": ("#E040FB", "#FFFFFF"), "Pause": ("#3A4670", "#FFFFFF"),
    "Essoufflement": ("#FF8A3D", "#2A1300"), "Retournement": ("#3D7BFF", "#FFFFFF"),
    "Retracement": ("#22D3EE", "#032A31"), "Zone de rebond": ("#FFC53D", "#241800"),
}


def e(x):
    return html.escape(str(x), quote=True)


def num(x, dec=1, signe=False):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    s = f"{x:+.{dec}f}" if signe else f"{x:.{dec}f}"
    return s.replace(".", ",").replace("-", "−")


def prix(x):
    if x is None or np.isnan(x):
        return "—"
    if x >= 1000:
        d = 1
    elif x >= 1:
        d = 3
    elif x >= 0.01:
        d = 5
    else:
        d = 8
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def heure(ts):
    return datetime.fromtimestamp(ts, TZ).strftime("%H:%M")


def date_courte(ts):
    mois = ["janv", "févr", "mars", "avr", "mai", "juin", "juil", "août", "sept", "oct", "nov", "déc"]
    d = datetime.fromtimestamp(ts, TZ)
    return f"{d.day} {mois[d.month - 1]}"


def duree(h):
    if h < 1:
        return "< 1 h"
    if h < 48:
        return f"{int(h)} h"
    return f"{int(h // 24)} j"


def tv(base):
    return f"https://www.tradingview.com/chart/?symbol={config.TV_PREFIXE}:{base}USDT.P"


def couleur_pct(p):
    if p is None or np.isnan(p):
        return "#F5F7FF"
    return "#B6FF3B" if p >= 0 else "#FF3D6E"


def mso_badge(v):
    if v is None or np.isnan(v):
        return '<span class="mso n">—</span>'
    if v >= config.MSO_SURACHAT:
        return f'<span class="mso ob">{v:.0f}</span><span class="sub">Surachat</span>'
    if v <= config.MSO_SURVENTE:
        return f'<span class="mso os">{v:.0f}</span><span class="sub">Survente</span>'
    return f'<span class="mso n">{v:.0f}</span><span class="sub">Neutre</span>'


def score_html(s):
    pts = s["points"]
    coul = "#B6FF3B" if pts >= 4 else ("#FFC53D" if pts >= 3 else "#F5F7FF")
    barres = "".join(f'<i class="{"on" if k < pts else ""}"></i>' for k in range(5))
    pen = '<span class="pen" title="Pénalité">!</span>' if s["penalite"] else ""
    titre = ", ".join(s["raisons"]) or "aucune confirmation"
    sens = "▲ long" if s["sens"] == "long" else "▼ short"
    return (f'<div class="score" title="{e(titre)}"><div style="display:flex;align-items:center"><span style="color:{coul}">{pts}/5</span>{pen}</div>'
            f'<div class="bars">{barres}</div><span class="sub">{sens}</span></div>')


def anneau(pct, coul):
    if pct is None:
        pct = 0
    r = 38
    circ = 2 * np.pi * r
    plein = circ * pct / 100.0
    return (f'<svg width="92" height="92" viewBox="0 0 92 92" role="img" aria-label="{pct:.0f} %">'
            f'<circle cx="46" cy="46" r="{r}" stroke="#1A2340" stroke-width="10" fill="none"/>'
            f'<circle cx="46" cy="46" r="{r}" stroke="{coul}" stroke-width="10" fill="none" stroke-linecap="round" '
            f'stroke-dasharray="{plein:.1f} {circ:.1f}" transform="rotate(-90 46 46)"/>'
            f'<text x="46" y="52" text-anchor="middle" fill="#F5F7FF" font-family="JetBrains Mono,monospace" '
            f'font-size="20" font-weight="700">{pct:.0f}%</text></svg>')


def courbe(vals, coul):
    v = [x for x in vals if x is not None]
    if len(v) < 2:
        return '<div class="sub">Courbe dispo après quelques heures</div>'
    mn, mx = min(v), max(v)
    rng = (mx - mn) or 1.0
    pts = " ".join(f"{i * 240 / (len(v) - 1):.1f},{40 - (x - mn) / rng * 34:.1f}" for i, x in enumerate(v))
    return (f'<svg width="100%" height="44" viewBox="0 0 240 44" preserveAspectRatio="none" aria-hidden="true">'
            f'<polyline points="{pts}" fill="none" stroke="{coul}" stroke-width="3" stroke-linejoin="round" '
            f'stroke-linecap="round"/></svg>')


def delta(d, unite=" pts"):
    if d is None:
        return '<span class="sub">direction dispo dans quelques heures</span>'
    c = "#B6FF3B" if d > 0 else ("#FF3D6E" if d < 0 else "#F5F7FF")
    fl = "▲" if d > 0 else ("▼" if d < 0 else "■")
    return f'<span style="color:{c}">{fl} {num(d, 1, True)}{unite}</span>'


CSS = """
*{box-sizing:border-box}body{margin:0;background:#06070D;color:#F5F7FF;font-family:Inter,system-ui,sans-serif}
a{color:#22D3EE;text-decoration:none}a:hover{color:#7DEBFF}
.wrap{max-width:1360px;margin:0 auto;padding:28px clamp(14px,3vw,40px) 48px;display:flex;flex-direction:column;gap:22px}
.h{font-family:'Space Grotesk',sans-serif;font-weight:700}
h2{margin:0;font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:700}
.card{background:#0C0F1C;border:1px solid #1E2A4A;border-radius:22px;padding:20px}
.sub{font-size:12px;color:#DCE2FF}.lbl{font-size:13px;color:#B9C2FF}
.mono{font-family:'JetBrains Mono',monospace}
.pill{display:inline-flex;align-items:center;gap:8px;padding:9px 14px;border-radius:999px;font-size:13px}
.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.tile{display:flex;flex-direction:column;gap:4px;padding:14px;border-radius:16px}
.row2{display:flex;flex-wrap:wrap;gap:14px;align-items:flex-start}
.filters{display:flex;flex-wrap:wrap;gap:8px}
.filters button{min-height:44px;padding:0 16px;border-radius:999px;font:600 14px Inter,sans-serif;cursor:pointer;background:#0D1220;color:#DCE2FF;border:1px solid #263155}
.filters button.on{background:#F5F7FF;color:#06070D;border-color:#F5F7FF}
.scroll{overflow-x:auto}
.mv{display:grid;grid-template-columns:96px 110px 80px minmax(140px,1fr) 140px 104px 110px;gap:12px;align-items:center;padding:12px 14px;border-radius:14px;background:#10152A;border:1px solid #1E2A4A;min-width:880px}
.mv.hd{background:none;border:none;padding:0 14px;font-size:12px;color:#B9C2FF}
.score{display:flex;flex-direction:column;gap:4px;font:700 16px 'JetBrains Mono',monospace}
.bars{display:flex;gap:3px}.bars i{width:12px;height:6px;border-radius:3px;background:#1F2A4D}.bars i.on{background:#B6FF3B}
.pen{display:inline-block;margin-left:6px;padding:0 6px;border-radius:6px;background:#FF3D6E;color:#fff;font-size:12px}
.bar{flex:1;height:8px;border-radius:99px;background:#1A2340;overflow:hidden}.bar b{display:block;height:100%;border-radius:99px}
.phase{justify-self:start;padding:6px 12px;border-radius:10px;font-size:13px;font-weight:700}
.mso{align-self:flex-start;padding:3px 9px;border-radius:8px;font:700 14px 'JetBrains Mono',monospace}
.mso.ob{background:#FF3D6E;color:#fff}.mso.os{background:#B6FF3B;color:#0B1400}.mso.n{background:#1A2340;color:#F5F7FF}
.col{display:flex;flex-direction:column;gap:2px}
.grp{display:flex;flex-direction:column;gap:8px;padding:14px;border-radius:16px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{padding:6px 11px;border-radius:9px;font-size:13px;font-weight:600}
.empty{font-size:13px;color:#DCE2FF;padding:8px 0}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:620px}
th{font-size:12px;color:#B9C2FF;text-align:left;font-weight:500;padding:6px 10px}
td{padding:10px;border-top:1px solid #1E2A4A}
.hide{display:none!important}
"""

JS = """
document.querySelectorAll('.filters button').forEach(function(b){b.addEventListener('click',function(){
 document.querySelectorAll('.filters button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');
 var f=b.dataset.f;document.querySelectorAll('[data-g]').forEach(function(el){
  var ok=f==='Tout'||(f==='Crypto'&&el.dataset.g==='crypto')||(f==='TradFi'&&el.dataset.g==='tradfi')||el.dataset.s===f;
  el.classList.toggle('hide',!ok);});});});
"""


def _attr(t):
    return f'data-g="{"tradfi" if t["tradfi"] else "crypto"}" data-s="{e(t["secteur"])}"'


def generer(r):
    """r = résultats du run (voir main.py)."""
    me = r["meteo"]
    maj = r["maintenant"]
    prochain = maj + 3600
    regime, regime_txt = r["regime_btc"]
    reg_coul = {"Haussier": ("#B6FF3B", "#0B1400"), "Baissier": ("#FF3D6E", "#FFFFFF")}.get(regime, ("#FFC53D", "#241800"))
    verts = me.get("verts")
    v_coul = "#B6FF3B" if (verts or 0) >= 50 else "#FF3D6E"
    e50 = me.get("ema50")
    e_coul = "#B6FF3B" if (e50 or 0) >= 50 else "#FF3D6E"
    f_moy = me.get("funding_moy")
    oi_d = me.get("oi_d24_pct")

    p = []
    p.append(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="{config.PAGE_RECHARGE_SEC}">
<title>{config.NOM}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="wrap">""")

    # ─── En-tête ────────────────────────────────────────────────────────────
    p.append(f"""<header style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:16px">
<div style="display:flex;align-items:center;gap:14px">
<div style="width:44px;height:44px;border-radius:14px;background:#B6FF3B;display:flex;align-items:center;justify-content:center">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0B1400" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/></svg></div>
<div style="display:flex;flex-direction:column"><span class="h" style="font-size:26px;letter-spacing:-.5px">{config.NOM}</span>
<span class="lbl">Perps USDT Bybit · {r['nb_crypto']} crypto · {r['nb_tradfi']} TradFi</span></div></div>
<div style="display:flex;flex-wrap:wrap;gap:10px">
<span class="pill" style="background:#0E1A12;border:1px solid #2E5A1A;color:#B6FF3B"><span style="width:8px;height:8px;border-radius:50%;background:#B6FF3B"></span>À jour · {heure(maj)} Toronto</span>
<span class="pill" style="background:#0D1220;border:1px solid #263155;color:#DCE2FF">Prochain scan vers {heure(prochain)}</span>
</div></header>""")

    # ─── Filtres ────────────────────────────────────────────────────────────
    btns = ['<button type="button" class="on" data-f="Tout">Tout</button>',
            '<button type="button" data-f="Crypto">Crypto</button>',
            '<button type="button" data-f="TradFi">TradFi</button>']
    for s in r["secteurs_filtres"]:
        btns.append(f'<button type="button" data-f="{e(s)}">{e(s)}</button>')
    p.append(f'<nav class="filters" aria-label="Filtres">{"".join(btns)}</nav>')

    # ─── Météo ──────────────────────────────────────────────────────────────
    p.append(f"""<section class="grid4" aria-label="Météo du marché">
<div class="card" style="display:flex;align-items:center;gap:18px">{anneau(verts, v_coul)}
<div style="display:flex;flex-direction:column;gap:4px"><span class="lbl">Tokens verts 24 h</span>
<span class="h" style="font-size:22px;color:{v_coul}">{"Marché vert" if (verts or 0) >= 50 else "Marché rouge"}</span>
<span style="font-size:13px">{delta(me.get('verts_d4'))} en 4 h</span><span style="font-size:13px">{delta(me.get('verts_d24'))} en 24 h</span></div></div>
<div class="card" style="display:flex;flex-direction:column;gap:8px"><span class="lbl">Au-dessus de l'EMA50 4H</span>
<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap"><span class="mono" style="font-size:36px;font-weight:700">{num(e50, 0)}%</span>
<span style="font-size:13px">{delta(me.get('ema50_d24'))} 24 h</span></div>{courbe(me.get('historique_ema50', []), e_coul)}</div>
<div class="card" style="display:flex;flex-direction:column;gap:10px"><span class="lbl">Régime BTC 4H</span>
<span class="h" style="align-self:flex-start;padding:8px 14px;border-radius:12px;background:{reg_coul[0]};color:{reg_coul[1]};font-size:18px">{e(regime)}</span>
<span class="sub" style="font-size:13px">{e(regime_txt)}</span></div>
<div class="card" style="display:flex;flex-direction:column;gap:10px"><span class="lbl">Funding moyen · OI total</span>
<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap"><span class="mono" style="font-size:28px;font-weight:700;color:#22D3EE">{num(f_moy * 100 if f_moy is not None else None, 4, True)}%</span>
<span class="mono" style="font-size:18px;color:#A78BFA">OI {num(oi_d, 1, True) + " %" if oi_d is not None else "—"} 24 h</span></div>
<span class="sub" style="font-size:13px">{"Foule plutôt longue" if (f_moy or 0) > 0.0001 else ("Foule plutôt courte" if (f_moy or 0) < -0.0001 else "Foule équilibrée")}</span></div>
</section>""")

    # ─── Rotation des secteurs ──────────────────────────────────────────────
    tiles = []
    for s in r["rotation"]:
        up = s["pct"] >= 0
        bg, bd, fg = ("#12260A", "#4C8A1C", "#B6FF3B") if up else ("#2A0A14", "#8A1C3A", "#FF6B8E")
        g = "tradfi" if s["tradfi"] else "crypto"
        tiles.append(f'<div class="tile" data-g="{g}" data-s="{e(s["nom"])}" style="background:{bg};border:1px solid {bd};color:{fg}">'
                     f'<span style="font-size:13px;font-weight:600">{e(s["nom"])}</span>'
                     f'<span class="mono" style="font-size:22px;font-weight:700">{num(s["pct"], 1, True)}%</span>'
                     f'<span style="font-size:12px">{s["nb"]} {("contrat" if s["tradfi"] else "token") + ("s" if s["nb"] > 1 else "")}</span></div>')
    p.append(f"""<section class="card" aria-label="Rotation des secteurs" style="display:flex;flex-direction:column;gap:14px">
<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px"><h2>Rotation des secteurs</h2><span class="lbl">Variation moyenne 24 h</span></div>
<div class="tiles">{"".join(tiles) or '<div class="empty">Aucun secteur.</div>'}</div></section>""")

    # ─── Carnet des movers ──────────────────────────────────────────────────
    rows = ['<div class="mv hd"><span>Score</span><span>Token</span><span>Move</span><span>Retracement</span><span>Phase</span><span>MSO 4H</span><span>Depuis</span></div>']
    for mv in r["movers"]:
        t = mv["token"]
        ph = mv["e"]["phase"]
        bg, fg = PHASE_COUL.get(ph, ("#1A2340", "#FFFFFF"))
        retr = max(0.0, min(1.0, mv["e"]["retr"])) * 100
        mp = mv["e"]["move_pct"]
        new = ' <span class="chip" style="padding:1px 6px;background:#062027;border:1px solid #0E7490;color:#7DEBFF;font-size:11px">🆕</span>' if t["nouveau"] else ""
        rows.append(f"""<div class="mv" {_attr(t)}>{score_html(mv['score'])}
<div class="col"><a class="h" style="font-size:16px" href="{tv(t['base'])}" target="_blank" rel="noopener">{e(t['base'])}</a><span class="sub">{e(t['secteur'])}{new}</span></div>
<span class="mono" style="font-size:16px;font-weight:700;color:{couleur_pct(mp)}">{num(mp, 0, True)}%</span>
<div style="display:flex;align-items:center;gap:10px"><div class="bar"><b style="width:{retr:.0f}%;background:{bg}"></b></div><span class="mono" style="font-size:13px;width:44px">{retr:.0f}%</span></div>
<span class="phase" style="background:{bg};color:{fg}">{e(ph)}</span>
<div class="col">{mso_badge(t['m']['mso4h'])}</div>
<span style="font-size:13px;color:#DCE2FF">{duree(mv['e']['phase_depuis_h'])} · le {date_courte(mv['e']['capture_ts'])}</span></div>""")
    if not r["movers"]:
        rows.append('<div class="empty">Aucun mover suivi pour l\'instant : le carnet se remplit dès qu\'un token bouge de ±15 % sur 24 h.</div>')
    carnet_html = f"""<section class="card" aria-label="Carnet des movers" style="flex:999 1 760px;min-width:0;display:flex;flex-direction:column;gap:12px">
<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px"><h2>Carnet des movers</h2><span class="lbl">Triés par score de confirmations · {len(r['movers'])} suivis</span></div>
<div class="scroll"><div style="display:flex;flex-direction:column;gap:8px">{"".join(rows)}</div></div></section>"""

    # ─── BB 4H ──────────────────────────────────────────────────────────────
    grp_def = [
        ("probable", "Retournement probable", "Mèche 0,5–2 % hors bande, close dedans, moyenne à plat, divergence RSI 1H", "#12260A", "#4C8A1C", "#B6FF3B", "#1C3A0E", "#D8FFA0"),
        ("sans", "Touche sans confirmation", "À surveiller, il manque au moins une condition", "#2A1A03", "#8A6210", "#FFC53D", "#3A2606", "#FFE3A0"),
        ("marche", "Marche sur la bande", "Tendance forte : ne pas jouer contre", "#2A0A14", "#8A1C3A", "#FF6B8E", "#3D0E1E", "#FFC2D2"),
    ]
    bb_html = []
    for cat, titre, regle, bg, bd, fg, cbg, cfg in grp_def:
        items = r["bb"].get(cat, [])
        chips = []
        for it in items:
            t = it["token"]
            fl = "▲" if it["bb"]["sens"] == "long" else "▼"
            tip = f"{it['score']['points']}/5 · {', '.join(it['score']['raisons']) or 'aucune confirmation'} · touche il y a {it['bb']['bougies_depuis']} bougie(s) 4H · mèche {num(it['bb']['meche'], 2)} %"
            chips.append(f'<a class="chip" {_attr(t)} href="{tv(t["base"])}" target="_blank" rel="noopener" title="{e(tip)}" '
                         f'style="background:{cbg};border:1px solid {bd};color:{cfg}">{fl} {e(t["base"])} <span class="mono">{it["score"]["points"]}/5</span></a>')
        bb_html.append(f"""<div class="grp" style="background:{bg};border:1px solid {bd}">
<div style="display:flex;justify-content:space-between;align-items:center"><span style="font-weight:700;font-size:15px;color:{fg}">{titre}</span><span class="mono" style="font-size:13px">{len(items)}</span></div>
<span class="sub">{regle}</span><div class="chips">{"".join(chips) or '<span class="sub">Aucun</span>'}</div></div>""")

    comp = "".join(f'<a class="chip" {_attr(c["token"])} href="{tv(c["token"]["base"])}" target="_blank" rel="noopener" title="Largeur = {num(c["ratio"] * 100, 0)} % du minimum 90 j" '
                   f'style="background:#1B1036;border:1px solid #5B3BB0;color:#D9CCFF">{e(c["token"]["base"])}</a>' for c in r["compression"])
    nouv = "".join(f'<a class="chip" {_attr(n)} href="{tv(n["base"])}" target="_blank" rel="noopener" '
                   f'style="background:#062027;border:1px solid #0E7490;color:#7DEBFF">{e(n["base"])} · {n["jours"]} j '
                   f'<span style="color:{couleur_pct(n["pct24"])}">{num(n["pct24"], 0, True)}%</span></a>' for n in r["nouveaux"])
    cote = f"""<div style="flex:1 1 340px;min-width:0;display:flex;flex-direction:column;gap:14px">
<section class="card" aria-label="Touches BB 4H" style="display:flex;flex-direction:column;gap:12px"><h2>Touches BB 4H</h2>{"".join(bb_html)}</section>
<section class="card" aria-label="Compression et nouveaux" style="display:flex;flex-direction:column;gap:12px">
<h2>Compression 90 j</h2><span class="sub" style="font-size:13px">BB 4H au plus serré : un mouvement s'en vient, le sens reste à voir</span>
<div class="chips">{comp or '<span class="sub">Aucun token au plus serré</span>'}</div>
<h2 style="margin-top:6px">Nouveaux contrats</h2><span class="sub" style="font-size:13px">Lancés depuis moins de {config.JOURS_NOUVEAU} jours</span>
<div class="chips">{nouv or '<span class="sub">Aucun</span>'}</div></section></div>"""
    p.append(f'<div class="row2">{carnet_html}{cote}</div>')

    # ─── TradFi ─────────────────────────────────────────────────────────────
    lignes = []
    for t in r["tradfi"]:
        bb = t["m"]["bb"]
        bbt = "—" if not bb else {"probable": "Retournement probable", "sans": "Touche", "marche": "Marche sur la bande"}[bb["cat"]] + (" haut" if bb["cote"] == "haut" else " bas")
        ferme = '<span class="chip" style="padding:2px 8px;background:#1A2340;color:#DCE2FF">Marché fermé</span>' if t["m"]["ferme"] else ""
        lignes.append(f'<tr {_attr(t)}><td><a class="h" href="{tv(t["base"])}" target="_blank" rel="noopener">{e(t["base"])}</a> {ferme}</td>'
                      f'<td>{e(t["secteur"])}</td><td class="mono">{prix(t["last"])}</td>'
                      f'<td class="mono" style="color:{couleur_pct(t["pct24"])}">{num(t["pct24"], 2, True)}%</td>'
                      f'<td><div class="col">{mso_badge(t["m"]["mso4h"])}</div></td><td>{e(bbt)}</td></tr>')
    p.append(f"""<section class="card" aria-label="TradFi" style="display:flex;flex-direction:column;gap:12px">
<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px"><h2>TradFi</h2><span class="lbl">Actions, indices, métaux, énergie · hors météo crypto</span></div>
<div class="scroll"><table><thead><tr><th>Contrat</th><th>Secteur</th><th>Prix</th><th>24 h</th><th>MSO 4H</th><th>BB 4H</th></tr></thead>
<tbody>{"".join(lignes) or '<tr><td colspan="6" class="empty">Aucun contrat TradFi trouvé sur Bybit.</td></tr>'}</tbody></table></div></section>""")

    p.append(f"""<footer class="sub" style="text-align:center;padding-top:8px">{config.NOM} V{config.VERSION} · données Bybit · {r['nb_ok']} tokens analysés en {r['duree']:.0f} s · la page se recharge seule toutes les {config.PAGE_RECHARGE_SEC // 60} min</footer>""")
    p.append(f"</div><script>{JS}</script></body></html>")

    os.makedirs(config.DOSSIER_SITE, exist_ok=True)
    chemin = os.path.join(config.DOSSIER_SITE, "index.html")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("".join(p))
    return chemin
