"""
HKJC Race Data Scraper
Runs automatically via GitHub Actions on race days (Wed & Sat)
Saves results to data/races.json which the website reads
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, date
import time
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

def get_page(url, retries=3):
    """Fetch a page with retries."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None

def scrape_hkjc_racecard():
    """
    Scrape today's race card from HKJC.
    Returns list of race dicts with horse data.
    """
    print("Scraping HKJC race cards...")
    races = []

    # HKJC race entries page
    url = "https://racing.hkjc.com/racing/english/racing-info/entries_tab.aspx"
    r = get_page(url)
    if not r:
        print("  Could not fetch HKJC race card page")
        return races

    soup = BeautifulSoup(r.text, 'html.parser')

    # Detect track from page title or content
    track = "Sha Tin"
    page_text = soup.get_text().lower()
    if "happy valley" in page_text:
        track = "Happy Valley"
    elif "sha tin" in page_text:
        track = "Sha Tin"

    # Find race tables
    race_tables = soup.find_all('table', class_=re.compile(r'table_bd|race|entrie', re.I))
    if not race_tables:
        # Try broader search
        race_tables = soup.find_all('table')

    today = date.today().isoformat()
    race_num = 1

    for table in race_tables[:12]:  # max 12 races
        horses = []
        rows = table.find_all('tr')

        # Try to extract distance from table header or surrounding elements
        distance = "1200"
        parent_text = table.parent.get_text() if table.parent else ""
        dist_match = re.search(r'(\d{4})m', parent_text)
        if dist_match:
            distance = dist_match.group(1)

        for row in rows[1:]:  # skip header
            cols = row.find_all(['td', 'th'])
            if len(cols) < 3:
                continue

            cells = [c.get_text(strip=True) for c in cols]

            # Try to extract horse name, draw, jockey, trainer
            # HKJC table structure: No | Draw | Horse | Jockey | Trainer | Weight | ...
            horse_name = ""
            draw = ""
            jockey = ""
            trainer = ""

            # Look for horse name cell (usually has a link)
            name_link = row.find('a')
            if name_link:
                horse_name = name_link.get_text(strip=True)

            # Extract other fields by position
            if len(cells) >= 4:
                draw = cells[1] if cells[1].isdigit() else ""
                if not horse_name and len(cells) > 2:
                    horse_name = cells[2]
                if len(cells) > 3:
                    jockey = cells[3] if len(cells[3]) > 2 else ""
                if len(cells) > 4:
                    trainer = cells[4] if len(cells[4]) > 2 else ""

            if horse_name and len(horse_name) > 1 and horse_name not in ['Horse', 'Name', 'No.']:
                horses.append({
                    "name": horse_name,
                    "barrier": draw,
                    "jockey": jockey,
                    "trainer": trainer,
                    "odds": "",
                    "openingOdds": "",
                    "form": "",
                    "tipsters": "0",
                    "jockeyRate": "50",
                    "trainerRate": "50",
                    "trackRecord": "unknown"
                })

        if len(horses) >= 4:
            races.append({
                "race_num": str(race_num),
                "track": track,
                "date": today,
                "distance": distance,
                "going": "Good",
                "horses": horses
            })
            race_num += 1

    print(f"  Found {len(races)} race(s) with horse data")
    return races


def scrape_hkjc_odds(races):
    """
    Try to scrape current odds from HKJC.
    Updates odds field in each horse dict.
    """
    print("Scraping HKJC odds...")
    url = "https://racing.hkjc.com/racing/english/odds/odds_win_place.aspx"
    r = get_page(url)
    if not r:
        print("  Could not fetch odds page")
        return races

    soup = BeautifulSoup(r.text, 'html.parser')
    # Extract odds — HKJC odds tables have horse name + odds columns
    odds_data = {}
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all('td')]
            if len(cells) >= 3:
                # Look for pattern: horse name + numeric odds
                horse_name = cells[0] if len(cells[0]) > 2 else (cells[1] if len(cells) > 1 else "")
                odds_str = ""
                for cell in cells[1:]:
                    # Odds look like "3.5" or "12.0"
                    if re.match(r'^\d+\.?\d*$', cell.strip()):
                        odds_str = cell.strip()
                        break
                if horse_name and odds_str:
                    odds_data[horse_name.upper()] = odds_str

    # Match odds to horses
    for race in races:
        for horse in race['horses']:
            name_upper = horse['name'].upper()
            if name_upper in odds_data:
                horse['odds'] = odds_data[name_upper]
                horse['openingOdds'] = odds_data[name_upper]

    matched = sum(1 for race in races for h in race['horses'] if h['odds'])
    print(f"  Matched odds for {matched} horse(s)")
    return races


def scrape_racenet_tips():
    """
    Scrape tips from Racenet Sha Tin tips page.
    Returns dict: {horse_name: tip_count}
    """
    print("Scraping Racenet tips...")
    tips = {}
    url = "https://www.racenet.com.au/horse-racing-tips/sha-tin"
    r = get_page(url)
    if not r:
        print("  Could not fetch Racenet (may be blocked)")
        return tips

    soup = BeautifulSoup(r.text, 'html.parser')
    # Look for horse names in tip sections
    tip_sections = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'tip|pick|select|runner', re.I))
    for sec in tip_sections:
        text = sec.get_text(strip=True)
        if 2 < len(text) < 40:
            name = text.strip()
            tips[name.upper()] = tips.get(name.upper(), 0) + 1

    print(f"  Found {len(tips)} tip mention(s) from Racenet")
    return tips


def scrape_everytip():
    """
    Scrape tips from Every Tip HK page.
    Returns dict: {horse_name: tip_count}
    """
    print("Scraping Every Tip HK...")
    tips = {}
    url = "https://www.everytip.co.uk/hong-kong-horse-racing-tips.html"
    r = get_page(url)
    if not r:
        print("  Could not fetch Every Tip")
        return tips

    soup = BeautifulSoup(r.text, 'html.parser')
    # Every Tip lists tips in structured format
    for el in soup.find_all(['strong', 'b', 'a', 'td']):
        text = el.get_text(strip=True)
        if 3 < len(text) < 35 and not any(c.isdigit() for c in text[:3]):
            tips[text.upper()] = tips.get(text.upper(), 0) + 1

    print(f"  Found {len(tips)} tip mention(s) from Every Tip")
    return tips


def count_tipster_backing(horse_name, all_tips):
    """Count how many tip sources back a given horse."""
    name_upper = horse_name.upper()
    # Check partial name match (first word) for robustness
    first_word = name_upper.split()[0] if name_upper.split() else name_upper
    count = 0
    for source_tips in all_tips:
        for tip_name in source_tips:
            if name_upper in tip_name or tip_name in name_upper or first_word in tip_name:
                count += 1
                break
    return min(count, 12)


def build_output(races, all_tips):
    """Assemble final JSON output."""
    for race in races:
        for horse in race['horses']:
            horse['tipsters'] = str(count_tipster_backing(horse['name'], all_tips))
    return {
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M HKT"),
        "source": "HKJC + Racenet + EveryTip",
        "races": races,
        "tip_sources_checked": len(all_tips),
        "note": "Odds and tips auto-populated. Review and adjust before using for betting decisions."
    }


def main():
    print("=" * 50)
    print(f"HKJC Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    # Scrape race cards
    races = scrape_hkjc_racecard()

    if races:
        # Try to get odds
        races = scrape_hkjc_odds(races)
    else:
        print("No race card data found. Creating empty template for today.")
        today = date.today().isoformat()
        races = [{
            "race_num": "1",
            "track": "Sha Tin",
            "date": today,
            "distance": "1200",
            "going": "Good",
            "horses": [],
            "note": "Auto-scrape found no data. Please enter horses manually."
        }]

    # Collect tips from multiple sources
    all_tips = []
    racenet_tips = scrape_racenet_tips()
    if racenet_tips:
        all_tips.append(racenet_tips)

    everytip_tips = scrape_everytip()
    if everytip_tips:
        all_tips.append(everytip_tips)

    # Build output
    output = build_output(races, all_tips)

    # Save to data/races.json
    os.makedirs("data", exist_ok=True)
    with open("data/races.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("=" * 50)
    print(f"Saved {len(races)} race(s) to data/races.json")
    print(f"Tip sources used: {len(all_tips)}")
    print("Done.")


if __name__ == "__main__":
    main()
