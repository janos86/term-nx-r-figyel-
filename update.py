"""Ingyenes napi frissítő: EUR/HUF (EKB) + hazai termelői árak (AKI/agrarunio). Hiba esetén a régi adat marad."""
import json, re, datetime, urllib.request

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

def num(s): return int(s.replace("\u00a0", "").replace(" ", "").replace(".", ""))

d = json.load(open("prices.json", encoding="utf-8"))
changed = False

# 1) Árfolyam
try:
    j = json.loads(get("https://api.frankfurter.dev/v1/latest?base=EUR&symbols=HUF"))
    d["fx"] = {"r": j["rates"]["HUF"], "d": "EKB, " + j["date"]}
    changed = True
except Exception as e:
    print("FX hiba:", e)

# 2) Hazai termelői árak: a sor első három száma = aktuális, korábbi, egy évvel korábbi
RANGES = {"Étkezési búza": (40000, 150000), "Takarmánykukorica": (40000, 150000), "Repcemag": (120000, 350000)}
try:
    html = get("https://www.agrarunio.hu/arfigyelo/10954-termenyarak")
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    for item in d["hu"]:
        key = item["n"]
        if key not in RANGES: continue
        lo, hi = RANGES[key]
        m = re.search(re.escape(key) + r"\W{0,6}((?:\d{1,3}(?:[ \u00a0.]\d{3}))(?:\D{1,6}\d{1,3}(?:[ \u00a0.]\d{3})){0,2})", text)
        if not m: continue
        vals = [num(v) for v in re.findall(r"\d{1,3}(?:[ \u00a0.]\d{3})", m.group(1))]
        if vals and lo <= vals[0] <= hi:
            item["p"] = vals[0]
            if len(vals) >= 2 and lo <= vals[1] <= hi: item["pr"] = vals[1]
            if len(vals) >= 3 and lo <= vals[2] <= hi: item["y"] = round((vals[0] / vals[2] - 1) * 100, 1)
            changed = True
except Exception as e:
    print("AKI hiba:", e)

if changed:
    d["updated"] = datetime.date.today().isoformat()
    json.dump(d, open("prices.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
