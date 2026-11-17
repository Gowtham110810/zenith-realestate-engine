import urllib.parse
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

PORTAL_BLACKLIST = {
    "99acres.com", "magicbricks.com", "housing.com", "nobroker.in",
    "squareyards.com", "commonfloor.com", "makaan.com", "justdial.com",
    "sulekha.com", "facebook.com", "instagram.com", "linkedin.com",
    "youtube.com", "quikr.com", "olx.in", "indiamart.com"
}


def deep_discover_urls(category: str, city: str):
    query = f'{category} in {city} official website contact email -99acres -magicbricks -housing -justdial'
    candidates = set()
    if DDGS:
        try:
            ddgs = DDGS()
            for r in ddgs.text(query, max_results=12):
                if r.get("href"):
                    candidates.add(r["href"])
        except Exception:
            pass

    final_urls = []
    for url in candidates:
        netloc = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
        if netloc and not any(b in netloc for b in PORTAL_BLACKLIST):
            final_urls.append(url)
    return final_urls
