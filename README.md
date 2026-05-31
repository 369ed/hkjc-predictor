# HKJC Racing Predictor — Setup Guide

Free website + automated scraping. No coding required beyond copy-paste.

---

## What you get

- A polished prediction website hosted free on GitHub Pages
- Automated HKJC race card scraping every Wednesday and Saturday at 8am HKT
- Tips aggregated from Racenet and Every Tip HK
- All prediction logic, bankroll tracking, and performance stats

---

## Step 1 — Create a free GitHub account

Go to https://github.com and sign up. It's free.

---

## Step 2 — Create a new repository

1. Click the **+** icon (top right) → **New repository**
2. Name it: `hkjc-predictor`
3. Set it to **Public** (required for free hosting)
4. Click **Create repository**

---

## Step 3 — Upload the files

In your new repository, click **Add file → Upload files**, then upload ALL of the following files maintaining the folder structure:

```
index.html                          ← main website
scraper.py                          ← scraping script
data/
  races.json                        ← auto-updated by scraper
.github/
  workflows/
    scrape.yml                      ← automation schedule
```

**Important:** The `.github` folder is hidden on Mac/Windows. Make sure to upload the `scrape.yml` file too — create the folders manually in GitHub's interface if needed.

### To create the .github/workflows/scrape.yml in GitHub:
1. In your repo, click **Add file → Create new file**
2. In the filename box, type: `.github/workflows/scrape.yml`
3. Paste the contents of `scrape.yml`
4. Click **Commit new file**

---

## Step 4 — Enable GitHub Pages (free hosting)

1. In your repo, click **Settings** tab
2. Click **Pages** in the left sidebar
3. Under "Branch", select `main` and folder `/` (root)
4. Click **Save**
5. Wait 2 minutes — your site will be live at:
   `https://YOUR-GITHUB-USERNAME.github.io/hkjc-predictor/`

---

## Step 5 — Enable GitHub Actions (automated scraping)

1. Click the **Actions** tab in your repo
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. Click **Auto-Scrape HKJC Race Data** in the left panel
4. Click **Run workflow → Run workflow** to test it immediately

The scraper will now run automatically every Wednesday and Saturday at 8am HKT, updating `data/races.json`, which your website reads automatically.

---

## How scraping works

Each race day, GitHub Actions:
1. Wakes up a free cloud computer
2. Runs `scraper.py` which fetches from HKJC + Racenet + EveryTip
3. Saves results to `data/races.json`
4. Commits and pushes the file back to your repo
5. Your website (GitHub Pages) automatically serves the updated file

**Limitations:**
- Some sites block automated scraping — the script falls back gracefully
- HKJC occasionally changes their HTML structure, which may break the scraper
- Tips from Facebook, SCMP, and subscription sites cannot be scraped automatically — enter these manually in the Horses tab

---

## Manual scrape trigger

Any time you want fresh data:
1. Go to Actions tab in your repo
2. Click **Auto-Scrape HKJC Race Data**
3. Click **Run workflow**

---

## Updating the scraper

If the scraper breaks (because HKJC changed their website), edit `scraper.py` directly in GitHub and commit the change. The next run will use the updated code.

---

## Cost

Everything used in this setup is **completely free**:
- GitHub account: free
- GitHub Pages hosting: free
- GitHub Actions (scraping automation): free (2,000 minutes/month included)
- No credit card required

---

## Responsible gambling

This tool is for research and analysis only. No prediction model guarantees results. Always set a daily loss limit and stick to it. Never bet money you cannot afford to lose.
