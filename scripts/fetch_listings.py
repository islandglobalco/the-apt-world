"""Fetch active Manhattan rentals from RentCast, score them against local medians,
and write data/listings.json for the site. Runs in GitHub Actions; the API key
comes from the RENTCAST_API_KEY repository secret and never reaches the browser.

Budget: RentCast's free plan allows 50 requests a month. Each run uses at most
MAX_PAGES requests (500 listings each)."""
import json, os, statistics, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

API = "https://api.rentcast.io/v1/listings/rental/long-term"
MAX_PAGES = 2
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "listings.json")

# Manhattan ZIP codes -> neighborhood (approximate; ZIPs cross some boundaries)
HOODS = {
 "10001":"Chelsea","10002":"Lower East Side","10003":"East Village","10004":"Financial District","10005":"Financial District",
 "10006":"Financial District","10007":"Tribeca","10009":"East Village","10010":"Gramercy","10011":"Chelsea","10012":"SoHo",
 "10013":"Tribeca","10014":"West Village","10016":"Murray Hill","10017":"Midtown East","10018":"Garment District",
 "10019":"Hell's Kitchen","10021":"Upper East Side","10022":"Midtown East","10023":"Upper West Side","10024":"Upper West Side",
 "10025":"Morningside Heights","10026":"Harlem","10027":"Harlem","10028":"Upper East Side","10029":"East Harlem",
 "10030":"Harlem","10031":"Hamilton Heights","10032":"Washington Heights","10033":"Washington Heights","10034":"Inwood",
 "10035":"East Harlem","10036":"Hell's Kitchen","10037":"Harlem","10038":"Financial District","10039":"Harlem",
 "10040":"Inwood","10044":"Roosevelt Island","10065":"Upper East Side","10069":"Upper West Side","10075":"Upper East Side",
 "10128":"Yorkville","10162":"Upper East Side","10280":"Battery Park City","10282":"Battery Park City",
}

def fetch(key):
    rows = []
    for page in range(MAX_PAGES):
        q = urllib.parse.urlencode({"city": "New York", "state": "NY", "status": "Active",
                                    "limit": 500, "offset": page * 500})
        req = urllib.request.Request(f"{API}?{q}", headers={"X-Api-Key": key, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            batch = json.load(r)
        rows += batch
        if len(batch) < 500:
            break
    return rows

def price_cuts(h):
    if not isinstance(h, dict):
        return 0
    prices = [v.get("price") for _, v in sorted(h.items()) if isinstance(v, dict) and v.get("price")]
    return sum(1 for a, b in zip(prices, prices[1:]) if b < a)

def score(rows):
    live = [r for r in rows if r.get("price") and r.get("zipCode") in HOODS and r.get("bedrooms") is not None]
    by_zip, by_beds = {}, {}
    for r in live:
        b = min(int(r["bedrooms"]), 3)
        by_zip.setdefault((r["zipCode"], b), []).append(r["price"])
        by_beds.setdefault(b, []).append(r["price"])
    kept, rejected = [], {"Overpriced": 0, "At market": 0}
    for r in live:
        b = min(int(r["bedrooms"]), 3)
        peers = by_zip[(r["zipCode"], b)]
        median = statistics.median(peers if len(peers) >= 5 else by_beds[b])
        under = median - r["price"]
        pct = under / median
        if pct < -0.10:
            rejected["Overpriced"] += 1; continue
        if pct < 0.04:
            rejected["At market"] += 1; continue
        cuts = price_cuts(r.get("history"))
        office = (r.get("listingOffice") or {})
        kept.append({
            "id": r.get("id"), "address": r.get("addressLine1") or r.get("formattedAddress"), "unit": r.get("addressLine2") or "",
            "zip": r["zipCode"], "hood": HOODS[r["zipCode"]], "beds": r["bedrooms"], "baths": r.get("bathrooms"),
            "sqft": r.get("squareFootage"), "built": r.get("yearBuilt"), "type": r.get("propertyType"),
            "price": r["price"], "median": round(median), "under": round(under), "pct": round(pct * 100, 1),
            "cuts": cuts, "dom": r.get("daysOnMarket"), "listed": r.get("listedDate"), "seen": r.get("lastSeenDate"),
            "office": office.get("name"), "officePhone": office.get("phone"), "officeSite": office.get("website"),
            "lat": r.get("latitude"), "lng": r.get("longitude"),
        })
    kept.sort(key=lambda x: (x["pct"] + 2 * x["cuts"]), reverse=True)
    return live, kept, rejected

def main():
    key = os.environ.get("RENTCAST_API_KEY")
    if not key:
        sys.exit("RENTCAST_API_KEY is not set")
    rows = fetch(key)
    live, kept, rejected = score(rows)
    out = {"source": "RentCast", "market": "Manhattan", "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="minutes"),
           "fetched": len(rows), "analyzed": len(live), "kept": len(kept), "rejected": rejected, "listings": kept[:60]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(f"fetched {len(rows)}, analyzed {len(live)}, kept {len(kept)}, rejected {rejected}")

if __name__ == "__main__":
    main()
