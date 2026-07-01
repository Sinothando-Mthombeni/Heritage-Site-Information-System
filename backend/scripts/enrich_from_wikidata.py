"""
scripts/enrich_from_wikidata.py
================================
One-shot enrichment script: reads seed_data.json, queries Wikidata's SPARQL
endpoint for each site by its known QID, and writes an enriched JSON file
with Wikidata descriptions, coordinates (lat/lon), and Wikimedia Commons
image URLs merged into each site record.

Run ONCE manually — never at app startup — so the app has zero runtime
dependency on Wikidata availability.

Usage (from backend/):
    python scripts/enrich_from_wikidata.py

Output:
    heritage_backend/core/fixtures/seed_data_enriched.json

Network note:
    Requires https://query.wikidata.org/sparql
    This is NOT in the sandbox/CI allowlist — run locally only.
"""

import json
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed: pip install requests")

BASE_DIR    = Path(__file__).resolve().parent.parent
FIXTURE_IN  = BASE_DIR / "heritage_backend" / "core" / "fixtures" / "seed_data.json"
FIXTURE_OUT = BASE_DIR / "heritage_backend" / "core" / "fixtures" / "seed_data_enriched.json"

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "Accept": "application/sparql-results+json",
    # Wikidata requires a descriptive UA — bot-like agents get 403 without one
    "User-Agent": (
        "HeritageSiteIS-Portfolio-Enrichment/1.0 "
        "(https://github.com/Sinothando-Mthombeni/Heritage-Site-Information-System)"
    ),
}

# ---------------------------------------------------------------------------
# QID map: site name (exactly as in seed_data.json) -> Wikidata QID
# Verified at https://www.wikidata.org/wiki/<QID>
# Set to None for sites with no Wikidata entry — they are skipped gracefully.
# ---------------------------------------------------------------------------
SITE_QIDS = {
    # UNESCO World Heritage Sites
    "Cradle of Humankind":                           "Q173862",
    "iSimangaliso Wetland Park":                     "Q191085",
    "Robben Island":                                 "Q174527",
    "Maloti-Drakensberg Park":                       "Q1875940",
    "Mapungubwe Cultural Landscape":                 "Q1059712",
    "Cape Floral Region Protected Areas":            "Q15994",
    "Vredefort Dome":                                "Q210770",
    "Richtersveld Cultural and Botanical Landscape": "Q1358427",
    "Barberton Makhonjwa Mountains":                 "Q15987891",
    "Nelson Mandela Legacy Sites":                   "Q19830655",
    # Museums & Memorials
    "Apartheid Museum":                              "Q1018786",
    "Voortrekker Monument":                          "Q607693",
    "Constitution Hill":                             "Q2476620",
    "Hector Pieterson Memorial and Museum":          "Q1598408",
    "Castle of Good Hope":                           "Q740640",
    "District Six Museum":                           "Q1226527",
    "Nelson Mandela Museum":                         "Q6996895",
    "Anglo-Boer War Museum":                         "Q4763440",
    "Freedom Park":                                  "Q1440918",
    # Natural Reserves
    "Blyde River Canyon Nature Reserve":             "Q575226",
    "Addo Elephant National Park":                   "Q579788",
    "Pilanesberg National Park":                     "Q1948817",
    # Archaeological
    "Sterkfontein Caves":                            "Q507698",
    # Historical Monuments
    "Pilgrim's Rest Historic Village":               "Q1941869",
    "Ncome (Blood River) Monument":                  "Q1753574",
    # Cultural Villages
    "Shakaland Zulu Cultural Village":               "Q7459065",
    "Botshabelo Ndebele Village":                    None,
    # khomani has special character
    "\u01c2Khomani Cultural Landscape":              "Q16857009",
}


def sparql_query(qids):
    values_clause = " ".join(f"wd:{q}" for q in qids)
    query = f"""
SELECT ?item ?description ?coord ?image WHERE {{
  VALUES ?item {{ {values_clause} }}
  OPTIONAL {{
    ?item schema:description ?description .
    FILTER(LANG(?description) = "en")
  }}
  OPTIONAL {{ ?item wdt:P625 ?coord . }}
  OPTIONAL {{ ?item wdt:P18 ?image . }}
}}
"""
    resp = requests.get(SPARQL_ENDPOINT, params={"query": query, "format": "json"},
                        headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_coord(wkt):
    """'Point(28.25 -25.92)' -> (lat, lon)"""
    m = re.match(r"Point\(([0-9.\-]+)\s+([0-9.\-]+)\)", wkt or "")
    if not m:
        return None, None
    return float(m.group(2)), float(m.group(1))  # WKT is lon lat, we want lat lon


def qid_from_url(url):
    return url.rstrip("/").split("/")[-1]


def run():
    if not FIXTURE_IN.exists():
        sys.exit(f"Fixture not found: {FIXTURE_IN}\nRun from backend/ directory.")

    with open(FIXTURE_IN, encoding="utf-8") as f:
        fixture = json.load(f)

    # Index site records by name
    site_records = {
        rec["fields"]["name"]: rec
        for rec in fixture
        if rec["model"] == "core.heritagesite"
    }

    qid_to_name = {
        qid: name
        for name, qid in SITE_QIDS.items()
        if qid and name in site_records
    }

    if not qid_to_name:
        print("Nothing to enrich — no matching QIDs found.")
        return

    print(f"Fetching Wikidata enrichment for {len(qid_to_name)} sites...\n")
    enrichment = {}
    qids = list(qid_to_name.keys())

    for i in range(0, len(qids), 20):
        batch = qids[i:i + 20]
        print(f"  Batch {i // 20 + 1}: {len(batch)} QIDs")
        try:
            data = sparql_query(batch)
        except requests.HTTPError as e:
            print(f"  HTTP {e.response.status_code} — skipping batch")
            continue
        except Exception as e:
            print(f"  Error: {e} — skipping batch")
            continue

        for row in data["results"]["bindings"]:
            qid  = qid_from_url(row["item"]["value"])
            name = qid_to_name.get(qid)
            if not name:
                continue
            coord_raw = row.get("coord", {}).get("value")
            lat, lon  = parse_coord(coord_raw)
            image_raw = row.get("image", {}).get("value", "")
            enrichment[name] = {
                "wikidata_qid":         qid,
                "wikidata_description": row.get("description", {}).get("value"),
                "latitude":             lat,
                "longitude":            lon,
                "image_url":            image_raw if image_raw.startswith("http") else None,
            }
            print(f"    OK  {name}")

        time.sleep(1)   # Wikidata rate limit: ~1 req/sec for bots

    # Merge into fixture records
    for name, extra in enrichment.items():
        if name in site_records:
            site_records[name]["fields"].update(extra)

    # Write enriched fixture (preserving order)
    enriched = []
    for rec in fixture:
        if rec["model"] == "core.heritagesite":
            rec = site_records.get(rec["fields"]["name"], rec)
        enriched.append(rec)

    with open(FIXTURE_OUT, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    n_enriched = len(enrichment)
    n_total    = len(qid_to_name)
    print(f"\nDone. {n_enriched}/{n_total} sites enriched.")
    print(f"Output: {FIXTURE_OUT}")
    missing = set(qid_to_name.values()) - set(enrichment.keys())
    if missing:
        print(f"No Wikidata result for: {', '.join(sorted(missing))}")


if __name__ == "__main__":
    run()
