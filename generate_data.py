#!/usr/bin/env python3
"""Génère data.json pour WorldRank (tous les pays, ~24 catégories, 3 langues).
Sources : API World Bank (dernière valeur disponible) + REST Countries (noms fr/en/es).
Option : place un fichier passport.csv (iso3,score — ex. Henley Passport Index) à côté pour activer « Pire passeport ».
Usage : python3 generate_data.py   (Python 3.8+, aucune dépendance). Rang 1 = valeur la plus élevée."""
import csv, datetime, json, os, re, time, unicodedata, urllib.request

# (nom, code World Bank, inverser ?)  — inverser = le rang 1 est la PLUS PETITE valeur
CATS = [
 ("👥 Population","SP.POP.TOTL",0),("🗺️ Superficie","AG.SRF.TOTL.K2",0),("🔬 Minuscule","AG.SRF.TOTL.K2",1),
 ("💰 PIB","NY.GDP.MKTP.CD",0),("💵 PIB/habitant","NY.GDP.PCAP.CD",0),("❤️ Espérance de vie","SP.DYN.LE00.IN",0),
 ("🏙️ Densité","EN.POP.DNST",0),("✈️ Tourisme","ST.INT.ARVL",0),("🌳 Forêts","AG.LND.FRST.ZS",0),
 ("🌐 Internet","IT.NET.USER.ZS",0),("🏭 Émissions CO₂","EN.ATM.CO2E.KT",0),("🍼 Fécondité","SP.DYN.TFRT.IN",0),
 ("👶 Mortalité infantile","SP.DYN.IMRT.IN",0),("🏘️ Urbanisation","SP.URB.TOTL.IN.ZS",0),("🌾 Terres agricoles","AG.LND.AGRI.ZS",0),
 ("📦 Exportations","NE.EXP.GNFS.CD",0),("🎖️ Militaire","MS.MIL.XPND.CD",0),("🏦 Dette publique","GC.DOD.TOTL.GD.ZS",0),
 ("📈 Chômage","SL.UEM.TOTL.ZS",0),("📚 Alphabétisation","SE.ADT.LITR.ZS",0),("🛬 Immigration","SM.POP.TOTL",0),
 ("🔥 Inflation","FP.CPI.TOTL.ZG",0),("🧓 Plus de 65 ans","SP.POP.65UP.TO.ZS",0),
]
MIN_COVERAGE, MIN_CATS_PER_COUNTRY = 0.6, 12

def get(url):
    err = None
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "WorldRank/1.0"}), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    raise SystemExit(f"Échec : {url} ({err})")

def wb_countries():
    out, page = {}, 1
    while True:
        meta, rows = get(f"https://api.worldbank.org/v2/country?format=json&per_page=400&page={page}")
        for c in rows:
            if c["region"]["value"] != "Aggregates": out[c["id"]] = (c["iso2Code"], c["name"])
        if page >= meta["pages"]: return out
        page += 1

def wb_indicator(code):
    vals, page = {}, 1
    while True:
        data = get(f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=500&mrnev=1&page={page}")
        if len(data) < 2 or not data[1]: return vals
        for r in data[1]:
            if r.get("value") is not None and r.get("countryiso3code"): vals[r["countryiso3code"]] = r["value"]
        if page >= data[0]["pages"]: return vals
        page += 1

IDX = {}  # nom normalisé -> iso3 (pour rapprocher passport.csv)
ALIAS = {"türkiye":"Turkey","russian federation":"Russia","congo (rep.)":"Republic of the Congo","congo (dem. rep.)":"DR Congo",
 "cape verde islands":"Cape Verde","comoro islands":"Comoros","naoero":"Nauru","palau islands":"Palau","the gambia":"Gambia",
 "the bahamas":"Bahamas","hong kong (sar china)":"Hong Kong","macao (sar china)":"Macau","taiwan (chinese taipei)":"Taiwan",
 "palestinian territory":"Palestine","st. vincent and the grenadines":"Saint Vincent and the Grenadines",
 "st. kitts and nevis":"Saint Kitts and Nevis","st. lucia":"Saint Lucia","côte d'ivoire":"Ivory Coast","eswatini":"Eswatini"}

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", re.sub(r"^the ", "", s))

def names():
    d = get("https://restcountries.com/v3.1/all?fields=cca3,name,translations,altSpellings")
    for c in d: IDX[norm(c["name"]["common"])] = c["cca3"]
    for c in d:
        for n in [c["name"]["official"]] + c.get("altSpellings", []): IDX.setdefault(norm(n), c["cca3"])
    return {c["cca3"]: ((c["translations"].get("fra") or {}).get("common"), c["name"]["common"],
                        (c["translations"].get("spa") or {}).get("common")) for c in d}

def flag(iso2):
    return "".join(chr(0x1F1E6 + ord(ch) - 65) for ch in iso2.upper()) if len(iso2) == 2 else "🏳️"

def rank(values):  # rang 1 = plus grande valeur ; ex æquo = même rang
    first = {}
    for i, v in enumerate(sorted(values.values(), reverse=True), 1): first.setdefault(v, i)
    return {k: first[v] for k, v in values.items()}

def passport(countries):
    """Lit passport.csv (colonnes rank,country,visa_free_score — ou iso3,score). Score le plus bas = rang 1 (pire passeport)."""
    if not os.path.exists("passport.csv"): return None
    out, miss = {}, []
    with open("passport.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            name = (r.get("country") or "").strip()
            try: sc = float(r.get("visa_free_score") or r.get("score"))
            except (TypeError, ValueError): continue
            iso = (r.get("iso3") or "").strip().upper() or IDX.get(norm(ALIAS.get(name.lower(), name)))
            if iso in countries: out[iso] = -sc
            else: miss.append(name)
    if miss: print("Passeport : non reconnus ->", ", ".join(miss))
    return out

def build(countries, series, nm):
    """series : liste de (nom, valeurs{iso3:valeur}) déjà orientées (plus grand = rang 1)."""
    cats, ranks = [], []
    for name, vals in series:
        vals = {k: v for k, v in vals.items() if k in countries}
        cov = len(vals) / len(countries)
        print(f"{name:26s} couverture {cov:4.0%}" + ("" if cov >= MIN_COVERAGE else "  -> ignorée"))
        if cov >= MIN_COVERAGE: cats.append({"name": name}); ranks.append(rank(vals))
    rows = []
    for iso3, (iso2, en) in countries.items():
        r = [rk.get(iso3) for rk in ranks]
        if sum(x is not None for x in r) >= min(MIN_CATS_PER_COUNTRY, len(cats)):
            fr, e, es = nm.get(iso3, (None, None, None))
            rows.append({"n": fr or en, "e": e or en, "s": es or fr or en, "f": flag(iso2), "r": r})
    return {"generated": datetime.date.today().isoformat(), "source": "World Bank", "cats": cats, "countries": rows}

if __name__ == "__main__":
    countries = wb_countries(); print(len(countries), "pays/territoires")
    cache, series = {}, []
    for name, code, inv in CATS:
        cache[code] = cache.get(code) or wb_indicator(code)
        series.append((name, {k: (-v if inv else v) for k, v in cache[code].items()}))
    nm = names(); pp = passport(countries)
    if pp: series.append(("🛂 Pire passeport", pp))
    else: print("passport.csv absent : catégorie « Pire passeport » ignorée")
    out = build(countries, series, nm)
    with open("data.json", "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"data.json : {len(out['countries'])} pays, {len(out['cats'])} catégories")
