"""
Scrape job boards and filter design-related vacancies.
"""
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from config import (
    DATA_DIR,
    SEEN_JOBS_JSON,
    DESIGN_KEYWORDS,
    ensure_data_dir,
)


def _load_seen():
    ensure_data_dir()
    if not SEEN_JOBS_JSON.exists():
        return set()
    try:
        data = json.loads(SEEN_JOBS_JSON.read_text(encoding="utf-8"))
        return set(data.get("seen", []))
    except Exception:
        return set()


def _save_seen(seen):
    ensure_data_dir()
    SEEN_JOBS_JSON.write_text(
        json.dumps({"seen": list(seen)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _matches_design(job: dict) -> bool:
    """True if job is design-related by title, team, or description."""
    text = " ".join(
        str(job.get(k, "")).lower()
        for k in ("title", "team", "company", "description")
    )
    return any(kw in text for kw in DESIGN_KEYWORDS)


def scrape_wise_jobs(html: str, base_url: str) -> list[dict]:
    """
    Parse wise.jobs jobs page. Expects HTML with job cards containing
    links to /job/..., title, Team: X, Description.
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    # Links like /job/something-jid-123
    for a in soup.find_all("a", href=re.compile(r"/job/[-a-z0-9]+-jid-\d+")):
        href = a.get("href")
        if not href:
            continue
        job_url = urljoin(base_url, href)
        title = (a.get_text(strip=True) or "").strip()
        if not title or len(title) > 200:
            continue
        # Try to find parent card for Team and Description
        card = a.find_parent(["article", "div", "li"])
        team = ""
        desc = ""
        if card:
            card_text = card.get_text(separator=" ", strip=True)
            team_m = re.search(r"Team\s*[:\s]+(\w+)", card_text, re.I)
            if team_m:
                team = team_m.group(1)
            desc_m = re.search(r"Description\s*([^\n]+)", card_text, re.I | re.DOTALL)
            if desc_m:
                desc = desc_m.group(1)[:500].strip()
        jobs.append({
            "url": job_url,
            "title": title,
            "team": team,
            "company": "Wise",
            "description": desc or title,
        })
    # Dedupe by url
    seen_urls = set()
    out = []
    for j in jobs:
        if j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            out.append(j)
    return out


def scrape_generic(html: str, base_url: str) -> list[dict]:
    """
    Generic parser: find any links that look like job pages and have design-related text nearby.
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not href or href.startswith("#") or "javascript:" in href:
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        # Skip external, assets, auth
        if parsed.path in ("/", "") or any(x in parsed.path for x in ("/login", "/sign-in", "/blog", "/posts")):
            continue
        title = (a.get_text(strip=True) or "").strip()
        if len(title) < 5 or len(title) > 300:
            continue
        parent = a.find_parent(["article", "div", "li", "section"])
        context = (parent.get_text(separator=" ", strip=True) if parent else title).lower()
        if not any(kw in context for kw in DESIGN_KEYWORDS):
            continue
        jobs.append({
            "url": full_url,
            "title": title,
            "team": "",
            "company": parsed.netloc.replace("www.", "").split(".")[0] or "Company",
            "description": (parent.get_text(separator=" ", strip=True)[:500] if parent else title),
        })
    seen_urls = set()
    out = []
    for j in jobs:
        if j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            out.append(j)
    return out


def fetch_page(url: str, timeout: int = 15) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


def get_jobs_for_url(url: str) -> list[dict]:
    """Fetch URL, choose parser by domain, return list of job dicts."""
    html = fetch_page(url)
    parsed = urlparse(url)
    if "wise.jobs" in parsed.netloc:
        jobs = scrape_wise_jobs(html, url)
    else:
        jobs = scrape_generic(html, url)
    return [j for j in jobs if _matches_design(j)]


def get_new_jobs(urls: list[str]) -> list[dict]:
    """
    For each URL in urls, fetch and parse jobs; filter design; exclude already seen.
    Mark returned jobs as seen.
    """
    seen = _load_seen()
    new_jobs = []
    for url in urls:
        try:
            jobs = get_jobs_for_url(url)
            for j in jobs:
                job_id = j.get("url") or j.get("title", "")
                if job_id and job_id not in seen:
                    seen.add(job_id)
                    new_jobs.append(j)
        except Exception as e:
            # Log but don't fail whole run
            print(f"Error scraping {url}: {e}")
    _save_seen(seen)
    return new_jobs


if __name__ == "__main__":
    import sys
    from config import URLS_JSON
    if URLS_JSON.exists():
        data = json.loads(URLS_JSON.read_text(encoding="utf-8"))
        urls = data.get("urls", [])
    else:
        urls = ["https://wise.jobs/jobs"]
    jobs = get_new_jobs(urls)
    print(json.dumps(jobs, ensure_ascii=False, indent=2))
    print(f"\nTotal new design jobs: {len(jobs)}", file=sys.stderr)
