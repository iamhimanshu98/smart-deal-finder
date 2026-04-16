# ⚡ SmartDeal Finder

> **B.Tech Final Year Project** — AI-powered e-commerce price intelligence platform

SmartDeal Finder scrapes live product listings from multiple e-commerce platforms and uses a **K-Nearest Neighbors (KNN) machine learning algorithm** to surface the top 5 best deals — combining price, rating, and discount into a single **Deal Score**.

---

## 🎯 Project Highlights

| Feature | Details |
|---|---|
| **ML Algorithm** | K-Nearest Neighbors (KNN) via scikit-learn |
| **Scraping** | Selenium + BeautifulSoup (Amazon, Flipkart, Croma) |
| **Backend** | Python Flask REST API |
| **Visualization** | Plotly 3D scatter + Chart.js price history |
| **UI** | Dark glassmorphism, responsive design |
| **Extras** | Watchlist, deal score meter, price trend simulation |

---

## 🗂 Project Structure

```
smart-deal-finder/
├── app.py                  # Flask app — routes, caching, watchlist API
├── scraper.py              # Selenium scraper (Amazon/Flipkart/Croma)
├── recommender.py          # Standalone ML module (KNN + deal scoring)
├── templates/
│   ├── index.html          # Landing page with search UI
│   ├── results.html        # Results with cards, 3D plot, comparison table
│   └── watchlist.html      # Saved products page
├── static/
│   └── style.css           # Full design system (dark theme)
├── data/
│   └── watchlist/          # Persistent JSON watchlist
└── requirements.txt
```

---

## ⚙️ Setup & Installation

```bash
# 1. Clone the repo
git clone https://github.com/iamhimanshu98/smart-deal-finder.git
cd smart-deal-finder

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
.\venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Visit `http://localhost:5000`

> **Note**: Chrome must be installed. `webdriver-manager` auto-downloads the correct ChromeDriver.

---

## 🤖 How the KNN Algorithm Works

The recommender (`recommender.py`) treats each product as a point in 3D feature space:

- **X axis** — Price (inverted, so lower price = farther from origin)  
- **Y axis** — Discount percentage  
- **Z axis** — Customer rating

An **"ideal deal" point** is computed at (max_inverted_price, max_discount, max_rating). KNN finds the 5 real products **nearest** to this ideal point using Euclidean distance.

### Deal Score Formula

```
deal_score = (price_score × 50) + (rating_score × 30) + (discount_score × 20)
```

Each component is min-max normalized to [0, 1] before weighting.

---

## 📊 Features

### 🏠 Home Page
- Animated dark hero with glassmorphism UI
- Live source selection (Amazon / Flipkart / Croma)
- Advanced filters: max budget, minimum rating, sort order
- Quick popular searches

### 📋 Results Page
- Top 5 deal cards with:
  - Deal Score meter (animated progress bar)
  - 30-day simulated price history sparkline
  - Savings vs. 30-day average
  - Direct buy links
- Interactive 3D Plotly visualization (all products)
- Full comparison table
- Price distribution bar chart by platform
- "Watch" button to add to watchlist

### 🔔 Watchlist
- Persistent JSON-backed watchlist
- Add/remove products
- Quick access from navbar

### ⚡ Caching
- Results cached for 1 hour to avoid redundant scraping
- Cache freshness displayed on results page

---

## 🧠 Module Descriptions

### `app.py`
Flask application with routes:
- `GET /` — Home page
- `POST /search` — Search + scrape + recommend
- `GET /watchlist` — Watchlist page
- `GET/POST /api/watchlist` — Watchlist CRUD API
- `GET /api/price-history/<product>` — Price history API
- `GET /health` — Health check

### `scraper.py`
Selenium-based scraper:
- Handles Amazon (2 pages), Flipkart (3 pages), Croma
- Cleans URLs, extracts price/rating/discount
- Runs KNN (calls recommender logic) and saves CSV + Plotly JSON

### `recommender.py`
Pure ML module (no Selenium dependency):
- `clean_dataframe()` — Data cleaning pipeline
- `compute_deal_scores()` — Weighted deal scoring
- `recommend_top_n()` — KNN recommendation

---

## 📎 Tech Stack

- **Python 3.11+**
- **Flask 3.x** — Web framework
- **Selenium 4.x + webdriver-manager** — Browser automation
- **BeautifulSoup4** — HTML parsing
- **Pandas + NumPy** — Data processing
- **scikit-learn** — KNN & scaling
- **Plotly** — 3D visualization
- **Chart.js** (CDN) — Price history charts
- **Syne + DM Sans** (Google Fonts) — Typography

---

## ⚠️ Disclaimer

Web scraping is subject to the terms of service of each website. This project is for **educational purposes only**. Rate limiting and delays are implemented to be respectful. Always consult `robots.txt` before deploying in a production context.

---

## 👨‍💻 Author

**Himanshu** — B.Tech Final Year Student  
GitHub: [@iamhimanshu98](https://github.com/iamhimanshu98)
