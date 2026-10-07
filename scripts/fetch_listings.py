"""Fetch active Manhattan rentals from RentCast, score them against local medians,
and write data/listings.json for the site. Runs in GitHub Actions; the API key
comes from the RENTCAST_API_KEY repository secret and never reaches the browser.

Budget: RentCast's free plan allows 50 requests a month (hard-capped at 40 below). Each run uses at most
MAX_PAGES requests (500 listings each)."""
import json, os, statistics, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

API = "https://api.rentcast.io/v1/listings/rental/long-term"
MAX_PAGES = 2
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "listings.json")
LEDGER = os.path.join(os.path.dirname(__file__), "..", "data", "api_usage.json")
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw_listings.json")
RAW_FIELDS = ("id","formattedAddress","addressLine1","addressLine2","zipCode","bedrooms","bathrooms","squareFootage","yearBuilt","propertyType","price","listedDate","lastSeenDate","daysOnMarket","listingOffice","history","latitude","longitude")

# Hard budget. RentCast's free plan allows 50 requests a month; we stop at 40 so a
# miscount or a retry can never push us into paid overage. Every attempt counts,
# including failed ones, because RentCast counts those too.
MONTHLY_BUDGET = 40
MIN_HOURS_BETWEEN_FETCHES = 48

def load_ledger():
    try:
        with open(LEDGER) as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}

def save_ledger(led):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=1, sort_keys=True)

def month_key():
    return datetime.now(timezone.utc).strftime("%Y-%m")

def spend_one(led):
    """Record one request before it is sent. Refuse if the month's budget is used up."""
    m = month_key()
    used = led.setdefault("months", {}).get(m, 0)
    if used >= MONTHLY_BUDGET:
        raise SystemExit(f"Budget reached: {used}/{MONTHLY_BUDGET} requests used in {m}. Skipping until next month.")
    led["months"][m] = used + 1
    save_ledger(led)

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

def fetch(key, led):
    rows = []
    for page in range(MAX_PAGES):
        spend_one(led)
        q = urllib.parse.urlencode({"city": "New York", "state": "NY", "status": "Active",
                                    "limit": 500, "offset": page * 500})
        req = urllib.request.Request(f"{API}?{q}", headers={"X-Api-Key": key.strip(), "Accept": "application/json",
                                                         "User-Agent": "APT-listings/1.0 (+https://the-apt.world)"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                batch = json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:500]
            sys.exit(f"RentCast returned HTTP {e.code}: {body}")
        rows += batch
        if len(batch) < 500:
            break
    return rows

def price_cuts(h):
    if not isinstance(h, dict):
        return 0
    prices = [v.get("price") for _, v in sorted(h.items()) if isinstance(v, dict) and v.get("price")]
    return sum(1 for a, b in zip(prices, prices[1:]) if b < a)

TOO_GOOD = 0.40      # more than 40% under typical: likely a room, a lottery unit or bad data
MIN_PRICE = 1500     # below this in Manhattan, almost certainly not a whole apartment
MIN_PEERS = 8        # comparables needed for a neighborhood benchmark

def score(rows):
    live = [r for r in rows if r.get("price") and r.get("zipCode") in HOODS and r.get("bedrooms") is not None]
    by_hood, by_beds = {}, {}
    for r in live:
        b = int(r["bedrooms"])
        if b > 2:
            continue
        by_hood.setdefault((HOODS[r["zipCode"]], b), []).append(r["price"])
        by_beds.setdefault(b, []).append(r["price"])
    kept, rejected = [], {"Overpriced": 0, "At market": 0, "Too cheap to be real": 0, "3+ bedrooms": 0, "Too few comparables": 0}
    for r in live:
        b = int(r["bedrooms"])
        if b > 2:
            rejected["3+ bedrooms"] += 1; continue
        hood = HOODS[r["zipCode"]]
        peers = by_hood.get((hood, b), [])
        if len(peers) < MIN_PEERS:
            rejected["Too few comparables"] += 1; continue   # no fair local benchmark, so no verdict
        median = statistics.median(peers)
        under = median - r["price"]
        pct = under / median
        if r["price"] < MIN_PRICE or pct > TOO_GOOD:
            rejected["Too cheap to be real"] += 1; continue
        if pct < -0.10:
            rejected["Overpriced"] += 1; continue
        if pct < 0.04:
            rejected["At market"] += 1; continue
        cuts = price_cuts(r.get("history"))
        office = (r.get("listingOffice") or {})
        kept.append({
            "id": r.get("id"), "address": r.get("addressLine1") or r.get("formattedAddress"), "unit": r.get("addressLine2") or "",
            "zip": r["zipCode"], "hood": hood, "beds": r["bedrooms"], "baths": r.get("bathrooms"),
            "sqft": r.get("squareFootage"), "built": r.get("yearBuilt"), "type": r.get("propertyType"),
            "price": r["price"], "median": round(median), "under": round(under), "pct": round(pct * 100, 1),
            "benchmark": "neighborhood",
            "cuts": cuts, "dom": r.get("daysOnMarket"), "listed": r.get("listedDate"), "seen": r.get("lastSeenDate"),
            "office": office.get("name"), "officePhone": office.get("phone"), "officeSite": office.get("website"),
            "lat": r.get("latitude"), "lng": r.get("longitude"),
        })
    kept.sort(key=lambda x: (x["pct"] + 2 * x["cuts"]), reverse=True)
    return live, kept, rejected

def rents_by_hood(live):
    """Median asking rent per neighborhood and size (0=studio, 1, 2 bedrooms), only where 5+ listings."""
    groups = {}
    for r in live:
        b = int(r["bedrooms"])
        if b > 2:
            continue
        groups.setdefault(HOODS[r["zipCode"]], {}).setdefault(b, []).append(r["price"])
    out = {}
    for hood, sizes in groups.items():
        row = {str(b): {"median": round(statistics.median(v)), "n": len(v)} for b, v in sizes.items() if len(v) >= 5}
        if row:
            out[hood] = row
    return dict(sorted(out.items()))

def main():
    key = os.environ.get("RENTCAST_API_KEY")
    if not key:
        sys.exit("RENTCAST_API_KEY is not set")
    led = load_ledger()
    last = led.get("lastSuccess")
    have_raw = os.path.exists(RAW)
    rows, fetched_at = None, None
    if last and have_raw and os.environ.get("FORCE_REFRESH") != "1":
        hours = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 3600
        if hours < MIN_HOURS_BETWEEN_FETCHES:
            print(f"Last fetch was {hours:.0f}h ago (minimum {MIN_HOURS_BETWEEN_FETCHES}h). Rescoring saved listings; no API requests.")
            with open(RAW) as f:
                cached = json.load(f)
            rows, fetched_at = cached["rows"], cached["fetchedAt"]
    if rows is None:
        m = month_key()
        print(f"Budget before run: {led.get('months', {}).get(m, 0)}/{MONTHLY_BUDGET} requests used in {m}")
        rows = fetch(key, led)
        fetched_at = datetime.now(timezone.utc).isoformat(timespec="minutes")
        led["lastSuccess"] = fetched_at
        save_ledger(led)
        print(f"Budget after run: {led['months'][m]}/{MONTHLY_BUDGET} requests used in {m}")
        os.makedirs(os.path.dirname(RAW), exist_ok=True)
        with open(RAW, "w") as f:
            json.dump({"fetchedAt": fetched_at, "rows": [{k: r.get(k) for k in RAW_FIELDS} for r in rows]}, f, separators=(",", ":"))
    live, kept, rejected = score(rows)
    if not kept:
        print(f"No usable listings this run ({len(rows)} fetched). Keeping the previous data file.")
        return
    out = {"source": "RentCast", "market": "Manhattan", "fetchedAt": fetched_at,
           "fetched": len(rows), "analyzed": len(live), "kept": len(kept), "rejected": rejected, "rents": rents_by_hood(live), "listings": kept[:60]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(f"fetched {len(rows)}, analyzed {len(live)}, kept {len(kept)}, rejected {rejected}")

if __name__ == "__main__":
    main()
