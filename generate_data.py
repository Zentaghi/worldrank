#!/usr/bin/env python3
"""Génère data.json pour WorldRank (tous les pays, 20+ catégories).
Sources : API World Bank (valeur la plus récente disponible) + REST Countries (noms français).
Usage : python3 generate_data.py   (Python 3.8+, aucune dépendance)
Rang 1 = valeur la plus élevée de la statistique."""
import json, time, urllib.request, datetime

CATS = [
 ("👥 Population", "SP.POP.TOTL"), ("🗺️ Superficie", "AG.SRF.TOTL.K2"), ("💰 PIB", "NY.GDP.MKTP.CD"),
 ("💵 PIB/habitant", "NY.GDP.PCAP.CD"), ("❤️ Espérance de vie", "SP.DYN.LE00.IN"), ("🏙️ Densité", "EN.POP.DNST"),
 ("✈️ Tourisme", "ST.INT.ARVL"), ("🌳 Forêts", "AG.LND.FRST.ZS"), ("🌐 Internet", "IT.NET.USER.ZS"),
 ("🏭 Émissions CO₂", "EN.ATM.CO2E.KT"), ("🍼 Fécondité", "SP.DYN.TFRT.IN"), ("👶 Mortalité infantile", "SP.DYN.IMRT.IN"),
 ("🏘️ Urbanisation", "SP.URB.TOTL.IN.ZS"), ("🌾 Terres agricoles", "AG.LND.AGRI.ZS"), ("📦 Exportations", "NE.EXP.GNFS.CD"),
 ("🎖️ Dépenses militaires", "MS.MIL.XPND.CD"), ("📈 Chômage", "SL.UEM.TOTL.ZS"), ("📚 Alphabétisation", "SE.ADT.LITR.ZS"),
 ("🛬 Immigration", "SM.POP.TOTL"), ("🔥 Inflation", "FP.CPI.TOTL.ZG"), ("🧓 Plus de 65 ans", "SP.POP.65UP.TO.ZS"),
]
MIN_COVERAGE = 0.6      # une catégorie doit couvrir au moins 60 % des pays
MIN_CATS_PER_COUNTRY = 12

def get(url):
    err = None
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "WorldRank/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    raise SystemExit(f"Échec : {url} ({err})")

def wb_countries():
    out, page = {}, 1
    while True:
        meta, rows = get(f"https://api.worldbank.org/v2/country?format=json&per_page=400&page={page}")
        for c in rows:
            if c["region"]["value"] != "Aggregates":
                out[c["id"]] = (c["iso2Code"], c["name"])
        if page >= meta["pages"]: return out
        page += 1

def wb_indicator(code):
    vals, page = {}, 1
    while True:
        data = get(f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=500&mrnev=1&page={page}")
        if len(data) < 2 or not data[1]: return vals
        for r in data[1]:
            if r.get("value") is not None and r.get("countryiso3code"):
                vals[r["countryiso3code"]] = r["value"]
        if page >= data[0]["pages"]: return vals
        page += 1

def fr_names():
    d = get("https://restcountries.com/v3.1/all?fields=cca3,translations")
    return {c["cca3"]: (c.get("translations", {}).get("fra", {}) or {}).get("common") for c in d}

def flag(iso2):
    return "".join(chr(0x1F1E6 + ord(ch) - 65) for ch in iso2.upper()) if len(iso2) == 2 else "🏳️"

def rank(values):
    first = {}
    for i, v in enumerate(sorted(values.values(), reverse=True), 1):
        first.setdefault(v, i)
    return {k: first[v] for k, v in values.items()}

def build(countries, indicators, names):
    cats, ranks = [], []
    for (name, code), vals in zip(CATS, indicators):
        vals = {k: v for k, v in vals.items() if k in countries}
        cov = len(vals) / len(countries)
        print(f"{name:28s} {code:20s} couverture {cov:4.0%}" + ("" if cov >= MIN_COVERAGE else "  -> ignorée"))
        if cov >= MIN_COVERAGE:
            cats.append({"id": code, "name": name}); ranks.append(rank(vals))
    rows = []
    for iso3, (iso2, en) in countries.items():
        r = [rk.get(iso3) for rk in ranks]
        if sum(x is not None for x in r) >= min(MIN_CATS_PER_COUNTRY, len(cats)):
            rows.append({"n": names.get(iso3) or en, "f": flag(iso2), "r": r})
    return {"generated": datetime.date.today().isoformat(), "source": "World Bank (dernières valeurs disponibles)",
            "cats": cats, "countries": rows}

if __name__ == "__main__":
    countries = wb_countries()
    print(len(countries), "pays/territoires")
    out = build(countries, [wb_indicator(c) for _, c in CATS], fr_names())
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"data.json : {len(out['countries'])} pays, {len(out['cats'])} catégories")
