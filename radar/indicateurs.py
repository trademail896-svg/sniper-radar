"""
SNIPER RADAR — Indicateurs
==========================
Formules identiques à TradingView (Pine) :
- ta.sma / ta.ema / ta.rma (EMA et RMA amorcées par une SMA, comme Pine)
- ta.stdev (écart-type de population) → Bollinger
- ta.rsi (Wilder)
- ta.pivothigh / ta.pivotlow
- Heikin Ashi standard
- Market Structure Oscillator [LuxAlgo] : port ligne par ligne du code fourni par Dave
"""
import math
import numpy as np


def _nan(n):
    return np.full(n, np.nan)


def sma(x, n):
    x = np.asarray(x, dtype=float)
    out = _nan(len(x))
    if n <= 0 or len(x) < n:
        return out
    c = np.cumsum(np.insert(x, 0, 0.0))
    out[n - 1:] = (c[n:] - c[:-n]) / n
    return out


def _amorce_sma(x, n, alpha):
    x = np.asarray(x, dtype=float)
    out = _nan(len(x))
    if len(x) < n:
        return out
    prev = np.mean(x[:n])
    out[n - 1] = prev
    for i in range(n, len(x)):
        prev = alpha * x[i] + (1.0 - alpha) * prev
        out[i] = prev
    return out


def ema(x, n):
    return _amorce_sma(x, n, 2.0 / (n + 1.0))


def rma(x, n):
    return _amorce_sma(x, n, 1.0 / n)


def stdev_pop(x, n):
    x = np.asarray(x, dtype=float)
    out = _nan(len(x))
    for i in range(n - 1, len(x)):
        out[i] = np.std(x[i - n + 1:i + 1])
    return out


def bollinger(close, n, mult):
    mid = sma(close, n)
    sd = stdev_pop(close, n)
    return mid, mid + mult * sd, mid - mult * sd


def rsi(close, n):
    close = np.asarray(close, dtype=float)
    ch = np.diff(close, prepend=np.nan)
    up = np.where(ch > 0, ch, 0.0)
    dn = np.where(ch < 0, -ch, 0.0)
    up[0] = dn[0] = np.nan
    ru = rma(up[1:], n)
    rd = rma(dn[1:], n)
    out = _nan(len(close))
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(rd == 0, 100.0, np.where(ru == 0, 0.0, 100.0 - 100.0 / (1.0 + ru / rd)))
    out[1:] = r
    return out


def pivots_hauts(x, g, d):
    """Indices des pivots hauts confirmés (strict à gauche, ≥ à droite, comme Pine)."""
    x = np.asarray(x, dtype=float)
    res = []
    for i in range(g, len(x) - d):
        v = x[i]
        if np.isnan(v):
            continue
        if v > np.max(x[i - g:i]) and v >= np.max(x[i + 1:i + d + 1]):
            res.append(i)
    return res


def pivots_bas(x, g, d):
    x = np.asarray(x, dtype=float)
    res = []
    for i in range(g, len(x) - d):
        v = x[i]
        if np.isnan(v):
            continue
        if v < np.min(x[i - g:i]) and v <= np.min(x[i + 1:i + d + 1]):
            res.append(i)
    return res


def divergence_rsi(high, low, rsi_vals, g, d, fenetre):
    """
    Divergences confirmées dans les `fenetre` dernières bougies.
    Baissière : le prix fait un plus haut que le pivot précédent, le RSI un plus bas.
    Haussière : le prix fait un plus bas, le RSI un plus haut.
    """
    n = len(high)
    debut = n - 1 - fenetre
    out = {"haussiere": False, "baissiere": False}
    ph = [i for i in pivots_hauts(high, g, d) if i >= debut]
    if len(ph) >= 2:
        a, b = ph[-2], ph[-1]
        if high[b] > high[a] and rsi_vals[b] < rsi_vals[a]:
            out["baissiere"] = True
    pb = [i for i in pivots_bas(low, g, d) if i >= debut]
    if len(pb) >= 2:
        a, b = pb[-2], pb[-1]
        if low[b] < low[a] and rsi_vals[b] > rsi_vals[a]:
            out["haussiere"] = True
    return out


def heikin_ashi(o, h, l, c):
    o, h, l, c = (np.asarray(v, dtype=float) for v in (o, h, l, c))
    n = len(c)
    hc = (o + h + l + c) / 4.0
    ho = np.empty(n)
    ho[0] = (o[0] + c[0]) / 2.0
    for i in range(1, n):
        ho[i] = (ho[i - 1] + hc[i - 1]) / 2.0
    hh = np.maximum.reduce([h, ho, hc])
    hl = np.minimum.reduce([l, ho, hc])
    return ho, hh, hl, hc


# ════════════════════════════════════════════════════════════════════════════
# Market Structure Oscillator [LuxAlgo] — port du code Pine v5 fourni par Dave
# ════════════════════════════════════════════════════════════════════════════
class _Swings:
    __slots__ = ("last", "mid", "prev", "crossed")

    def __init__(self):
        self.last = self.mid = self.prev = math.nan
        self.crossed = False

    def update(self, price):                      # method updatePattern
        self.crossed = False
        self.prev, self.mid, self.last = self.mid, self.last, price

    def query(self, is_high):                     # method queryPatterns
        if is_high:
            return self.prev < self.mid and self.mid >= self.last
        return self.prev > self.mid and self.mid <= self.last


def _pine_max(a, b):
    return math.nan if (math.isnan(a) or math.isnan(b)) else max(a, b)


def _pine_min(a, b):
    return math.nan if (math.isnan(a) or math.isnan(b)) else min(a, b)


class _Normalize:
    """normalize(buy, sell, smooth) — une instance par appel (état `var` de Pine)."""

    def __init__(self, smooth):
        self.smooth = smooth
        self.os = 0
        self.os_prev = None
        self.mx = math.nan
        self.mn = math.nan
        self.vals = []

    def step(self, buy, sell, close):
        os_new = 1 if buy else (-1 if sell else self.os)
        p = self.os_prev
        gt = p is not None and os_new > p
        lt = p is not None and os_new < p
        self.mx = close if gt else (self.mx if lt else _pine_max(close, self.mx))
        self.mn = close if lt else (self.mn if gt else _pine_min(close, self.mn))
        self.os = os_new
        self.os_prev = os_new
        den = self.mx - self.mn
        v = (close - self.mn) / den if (not math.isnan(den) and den != 0) else math.nan
        self.vals.append(v)
        w = self.vals[-self.smooth:]
        if len(w) < self.smooth or any(math.isnan(x) for x in w):
            return math.nan
        return sum(w) / self.smooth * 100.0


def mso(o, h, l, c, poids=(1.0, 3.0, 2.0), lissage=1):
    """Retourne la série du Market Structure Oscillator (0–100)."""
    h = np.asarray(h, dtype=float)
    l = np.asarray(l, dtype=float)
    c = np.asarray(c, dtype=float)
    n = len(c)
    st_h, st_l, it_h, it_l, lt_h, lt_l = (_Swings() for _ in range(6))
    n1, n2, n3 = _Normalize(lissage), _Normalize(lissage), _Normalize(lissage)
    prev_c = {"it_h": False, "it_l": False, "lt_h": False, "lt_l": False}
    out = _nan(n)

    def q3(last, mid, prev, is_high):              # queryPatterns(fonction)
        if is_high:
            return prev < mid and mid >= last
        return prev > mid and mid <= last

    def structure(hh, hl, lh, ll, kh, kl, close, norm):
        bull = bear = False
        c_h = lh.query(True)
        if c_h and c_h != prev_c[kh]:
            hh.update(lh.mid)
        prev_c[kh] = c_h
        if close > hh.last and not hh.crossed:
            hh.crossed = True
            bull = True
        c_l = ll.query(False)
        if c_l and c_l != prev_c[kl]:
            hl.update(ll.mid)
        prev_c[kl] = c_l
        if close < hl.last and not hl.crossed:
            hl.crossed = True
            bear = True
        return norm.step(bull, bear, close)

    for i in range(n):
        close = c[i]
        # shortMarketStructure()
        bull = bear = False
        if i >= 2 and q3(h[i], h[i - 1], h[i - 2], True):
            st_h.update(h[i - 1])
        if close > st_h.last and not st_h.crossed:
            st_h.crossed = True
            bull = True
        if i >= 2 and q3(l[i], l[i - 1], l[i - 2], False):
            st_l.update(l[i - 1])
        if close < st_l.last and not st_l.crossed:
            st_l.crossed = True
            bear = True
        v1 = n1.step(bull, bear, close)
        v2 = structure(it_h, it_l, st_h, st_l, "it_h", "it_l", close, n2)
        v3 = structure(lt_h, lt_l, it_h, it_l, "lt_h", "lt_l", close, n3)
        num = den = 0.0
        for w, v in zip(poids, (v1, v2, v3)):
            if not math.isnan(v):
                num += w * v
                den += w
        out[i] = num / den if den > 0 else math.nan
    return out
