"""
data_refresh_boeing.py
Scrapes Boeing careers for open role counts by division/location.
Falls back to baseline data if site blocks scraping (common).
Writes data_boeing.json to the working directory.

Usage:
    python data_refresh_boeing.py
"""

import json, datetime, pathlib, urllib.request, urllib.error, re, sys

OUTPUT_FILE = pathlib.Path(__file__).parent / "data_boeing.json"

FALLBACK = {
    "bca": {
        "total": 1340,
        "locations": [
            {"city": "Seattle, WA",       "open": 526, "filled": 175},
            {"city": "Everett, WA",       "open": 200, "filled": 50},
            {"city": "Renton, WA",        "open": 180, "filled": 65},
            {"city": "California",        "open": 323, "filled": 90},
            {"city": "N. Charleston, SC", "open": 62,  "filled": 23},
            {"city": "Jacksonville, FL",  "open": 30,  "filled": 10},
            {"city": "Chicago, IL",       "open": 19,  "filled": 6},
        ]
    },
    "bgs": {
        "total": 50,
        "locations": [
            {"city": "Dallas, TX",        "open": 15, "filled": 5},
            {"city": "San Diego, CA",     "open": 20, "filled": 6},
            {"city": "Denver/Aurora, CO", "open": 15, "filled": 4},
        ]
    },
    "bds": {
        "total": 75,
        "locations": [
            {"city": "El Segundo, CA", "open": 25, "filled": 8},
            {"city": "St. Louis, MO",  "open": 50, "filled": 10},
        ]
    },
    "spirit": {
        "total": 107,
        "locations": [
            {"city": "Wichita, KS", "open": 107, "filled": 37},
        ]
    },
    "bietc": {
        "total": 130,
        "locations": [
            {"city": "Bengaluru, India", "open": 130, "filled": 40},
        ]
    },
    "betc": {
        "total": 15,
        "locations": [
            {"city": "São José dos Campos, Brazil", "open": 15, "filled": 5},
        ]
    },
    "wisk": {
        "total": 52,
        "locations": [
            {"city": "Mountain View, CA", "open": 52, "filled": 12},
        ]
    },
    "avionx": {
        "total": 20,
        "locations": [
            {"city": "Virtual/Remote", "open": 15, "filled": 4},
            {"city": "Bristol, UK",    "open": 5,  "filled": 1},
        ]
    },
    "aurora": {
        "total": 60,
        "locations": [
            {"city": "Cambridge, MA",   "open": 35, "filled": 10},
            {"city": "Manassas, VA",    "open": 15, "filled": 4},
            {"city": "Bridgewater, VA", "open": 10, "filled": 3},
        ]
    },
    "insitu": {
        "total": 50,
        "locations": [
            {"city": "Bingen, WA",    "open": 45, "filled": 10},
            {"city": "Hood River, OR","open": 5,  "filled": 2},
        ]
    },
    "totalRoles": 1559
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

SEARCH_URLS = {
    "bca":    "https://jobs.boeing.com/search-jobs?orgIds=1&alm=BCA",
    "bgs":    "https://jobs.boeing.com/search-jobs?orgIds=1&alm=BGS",
    "bds":    "https://jobs.boeing.com/search-jobs?orgIds=1&alm=BDS",
    "aurora": "https://jobs.boeing.com/search-jobs?orgIds=1&alm=Aurora",
    "insitu": "https://jobs.boeing.com/search-jobs?orgIds=1&alm=Insitu",
}

def try_scrape(url: str) -> int | None:
    """Returns an integer count if scrape succeeds, else None."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read().decode("utf-8", errors="ignore")
        # Boeing jobs page shows "X jobs" — try to extract
        m = re.search(r'([\d,]+)\s+job', html, re.IGNORECASE)
        if m:
            return int(m.group(1).replace(",", ""))
    except Exception as e:
        print(f"  Scrape failed for {url}: {e}")
    return None

def build_data():
    now      = datetime.datetime.utcnow()
    next_ref = now + datetime.timedelta(days=5)

    data = {
        "meta": {
            "lastRefreshed": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "nextRefresh":   next_ref.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sources":       ["jobs.boeing.com", "fallback"],
        },
        "boeing": {}
    }

    total = 0
    for bu, fallback_bu in FALLBACK.items():
        if bu == "totalRoles":
            continue
        url = SEARCH_URLS.get(bu)
        scraped = None
        if url:
            print(f"  Trying {bu}…", end=" ")
            scraped = try_scrape(url)
            if scraped:
                print(f"✓ {scraped} roles")
            else:
                print("→ using fallback")

        bu_data = dict(fallback_bu)
        if scraped:
            bu_data["total"] = scraped
            data["meta"]["sources"].insert(0, "jobs.boeing.com")

        data["boeing"][bu] = bu_data
        total += bu_data.get("total", 0)

    data["boeing"]["totalRoles"] = total
    return data

def main():
    print("\n🔄  Boeing data refresh starting…")
    data = build_data()

    OUTPUT_FILE.write_text(json.dumps(data, indent=2))
    print(f"\n✅  data_boeing.json written → {OUTPUT_FILE}")
    print(f"   Total roles tracked: {data['boeing']['totalRoles']}")
    print(f"   Last refreshed:      {data['meta']['lastRefreshed']}\n")

if __name__ == "__main__":
    main()
