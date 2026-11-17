import json, math, os, glob
from datetime import datetime, timezone

def EP(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()

def day_curve(comp):
    """Release-day hourly viewers for one comparable: dict hour(1..24) -> viewers."""
    try:
        t0 = EP(comp["day_start"])
    except Exception:
        return None
    per = {}
    for pt in comp.get("hourly") or []:
        try:
            idx = int(round((EP(pt["from"]) - t0) / 3600.0))
        except Exception:
            continue
        if 0 <= idx < 24 and pt.get("viewers") is not None:
            per.setdefault(idx, []).append(float(pt["viewers"]))
    if 0 not in per:
        return None
    out = {}
    for idx, vals in per.items():
        out[idx + 1] = sum(vals) / len(vals)
    # fill small gaps by log-linear interpolation between known hours
    ks = sorted(out)
    for h in range(1, 25):
        if h in out:
            continue
        lo = max([k for k in ks if k < h], default=None)
        hi = min([k for k in ks if k > h], default=None)
        if lo is not None and hi is not None:
            f = (h - lo) / (hi - lo)
            out[h] = math.exp(math.log(out[lo]) * (1 - f) + math.log(out[hi]) * f)
    if len(out) < 20:
        return None
    return out

def rolling(text):
    t = (text or "").lower()
    if "midnight" in t or "rolling" in t:
        return 1
    if "global unlock" in t or "simultaneous" in t or "single unlock" in t:
        return 0
    return -1

def wquantile(pairs, tau):
    """pairs: list of (value, weight). Weighted quantile with linear interpolation."""
    pairs = sorted(pairs)
    tot = sum(w for _, w in pairs)
    if tot <= 0:
        return pairs[len(pairs) // 2][0]
    target = tau * tot
    acc = 0.0
    for i, (v, w) in enumerate(pairs):
        acc += w
        if acc >= target:
            if i == 0:
                return v
            pv, pw = pairs[i - 1]
            frac = (target - (acc - w)) / w if w > 0 else 0.0
            return pv + (v - pv) * frac
    return pairs[-1][0]

SIGMA = 1.1
ROLL_BONUS = 2.5
ROLL_PEN = 0.6
CONSOLE_BONUS = 1.3
SPREAD = 0.0

def forecast(case):
    known = case.get("known") or []
    p = float(known[0]["viewers"]) if known else 1.0
    if p < 1.0:
        p = 1.0
    lp = math.log(p)
    notes = case.get("notes") or ""
    troll = rolling(notes)
    levels = case.get("levels") or [0.05, 0.25, 0.5, 0.75, 0.95]
    curves = []
    for comp in case.get("comparables") or []:
        c = day_curve(comp)
        if not c or c.get(1, 0) <= 0:
            continue
        v1 = c[1]
        # similarity weight: launch scale proximity on log scale
        d = math.log(v1) - lp
        w = math.exp(-(d * d) / (2 * SIGMA * SIGMA))
        # unlock-style match: rolling-midnight console launches behave alike
        cr = rolling(comp.get("unlock"))
        if troll == 1 and cr == 1:
            w *= ROLL_BONUS
        elif troll == 1 and cr == 0:
            w *= ROLL_PEN
        # console-only comparables match a console-only target better
        plats = (comp.get("platforms") or "").lower()
        if "pc" not in plats:
            w *= CONSOLE_BONUS
        curves.append((c, w))
    rows = []
    for h in range(2, 25):
        pairs = []
        for c, w in curves:
            if h in c and c[h] > 0:
                pairs.append((math.log(c[h]) - math.log(c[1]), w))
        if not pairs:
            qs = [p] * len(levels)
        else:
            qs = []
            med = wquantile(pairs, 0.5)
            for tau in levels:
                q = wquantile(pairs, tau)
                # modest spread widening: cross-launch dispersion understates
                # single-launch uncertainty late in the day
                q = med + (q - med) * (1.0 + SPREAD * (h - 2))
                qs.append(p * math.exp(q))
        for i in range(1, len(qs)):
            if qs[i] < qs[i - 1]:
                qs[i] = qs[i - 1]
        qs = [min(max(q, 1.0), 1e9) for q in qs]
        rows.append({"hour": h, "q": [round(q, 2) for q in qs]})
    return {"hours": rows}

def main():
    idir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    odir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(odir, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(idir, "*.in"))):
        with open(path, "r", encoding="utf-8") as f:
            case = json.load(f)
        out = forecast(case)
        name = os.path.basename(path)[:-3] + ".out"
        tmp = os.path.join(odir, name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(out, f)
        os.replace(tmp, os.path.join(odir, name))

if __name__ == "__main__":
    main()
