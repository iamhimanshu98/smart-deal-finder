from flask import Flask, render_template, request, jsonify, session
import subprocess
import pandas as pd
import plotly.express as px
import os
import json
import time
import random
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib

# https://smart-deal-finder-mmuc.onrender.com

app = Flask(__name__)
app.secret_key = "smart_deal_finder_2024_secret"

os.makedirs("static", exist_ok=True)
os.makedirs("static/cache", exist_ok=True)
os.makedirs("data/watchlist", exist_ok=True)

CACHE_EXPIRY_SECONDS = 3600  # 1 hour cache

# ─────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────

def get_cache_key(product, websites):
    raw = f"{product.lower()}{'_'.join(sorted(websites))}"
    return hashlib.md5(raw.encode()).hexdigest()

def get_product_csv(product):
    product_filename = product.replace(" ", "_").lower()
    return os.path.join("static", f"top5_{product_filename}.csv")

def get_product_plot(product):
    product_filename = product.replace(" ", "_").lower()
    return os.path.join("static", f"top5_{product_filename}_plot.json")

def get_combined_csv(product):
    product_filename = product.replace(" ", "_").lower()
    return os.path.join("static", f"{product_filename}_combined_products.csv")

def is_cache_fresh(product):
    csv_file = get_product_csv(product)
    if not os.path.exists(csv_file):
        return False
    age = time.time() - os.path.getmtime(csv_file)
    return age < CACHE_EXPIRY_SECONDS

def generate_price_history(base_price, days=30):
    """Generate realistic simulated price history for demo purposes."""
    history = []
    price = base_price
    today = datetime.now()
    for i in range(days, 0, -1):
        date = today - timedelta(days=i)
        # Simulate some price variation ±8%
        change = random.uniform(-0.04, 0.04)
        price = round(price * (1 + change), 0)
        price = max(price, base_price * 0.80)
        history.append({
            "date": date.strftime("%b %d"),
            "price": int(price)
        })
    history.append({"date": "Today", "price": int(base_price)})
    return history

def load_watchlist():
    wl_file = "data/watchlist/watchlist.json"
    if os.path.exists(wl_file):
        with open(wl_file, "r") as f:
            return json.load(f)
    return []

def save_watchlist(items):
    wl_file = "data/watchlist/watchlist.json"
    with open(wl_file, "w") as f:
        json.dump(items, f, indent=2)

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Render the home page."""
    # Pass some popular searches for quick picks
    popular = ["iPhone 16 Pro", "Samsung S24 Ultra", "Puma Shoes", "Samsung Washing Machine", "Iron Box"]
    watchlist = load_watchlist()
    return render_template('index.html', popular_searches=popular, watchlist_count=len(watchlist))


@app.route('/search', methods=['POST'])
def search():
    """Handle product search and return results."""
    product = ""
    websites = []
    try:
        product = request.form['product'].strip()
        websites = request.form.getlist('websites')
        use_cache = request.form.get('use_cache', 'true') == 'true'
        sort_by = request.form.get('sort_by', 'deal_score')
        budget_max = request.form.get('budget_max', '')
        min_rating = float(request.form.get('min_rating', '0'))

        if not product:
            return render_template('results.html', product="", deals=[], plot_json=None,
                                   websites=[], error="Please enter a product name.",
                                   stats={}, all_products=[])

        if len(websites) < 2:
            return render_template('results.html', product=product, deals=[], plot_json=None,
                                   websites=websites, error="Please select at least 2 websites.",
                                   stats={}, all_products=[])

        # Check cache first
        if use_cache and is_cache_fresh(product):
            print(f"[CACHE HIT] Using cached results for: {product}")
        else:
            print(f"\n=== Searching for: {product} ===")
            print(f"Selected websites: {', '.join(websites)}")
            websites_str = ",".join(websites)
            result = subprocess.run(
                ['python', 'scraper.py', product, websites_str],
                capture_output=True, text=True, timeout=600
            )
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error occurred"
                return render_template('results.html', product=product, deals=[], plot_json=None,
                                       websites=websites, error=f"Scraping failed: {error_msg[-500:]}",
                                       stats={}, all_products=[])

        csv_file = get_product_csv(product)
        combined_csv = get_combined_csv(product)

        if not os.path.exists(csv_file):
            return render_template('results.html', product=product, deals=[], plot_json=None,
                                   websites=websites, error=f"No results found for '{product}'.",
                                   stats={}, all_products=[])

        df = pd.read_csv(csv_file)
        if df.empty:
            return render_template('results.html', product=product, deals=[], plot_json=None,
                                   websites=websites, error=f"No deals found for '{product}'.",
                                   stats={}, all_products=[])

        # Apply filters
        if budget_max:
            try:
                df = df[df['Price_num'] <= float(budget_max)]
            except:
                pass
        if min_rating > 0:
            df = df[df['Rating_num'] >= min_rating]

        # Build deals list
        deals = []
        for idx, row in df.iterrows():
            url = str(row.get('URL', '#'))
            if not (url and url != 'N/A' and url.startswith('http')):
                product_name = row.get('Title', 'Product')
                src = row.get('Source', '')
                if 'Amazon' in src:
                    url = f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}"
                elif 'Flipkart' in src:
                    url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '+')}"
                else:
                    url = f"https://www.croma.com/search?q={product_name.replace(' ', '+')}"

            price_val = row.get('Price_num', 0)
            rating_val = row.get('Rating_num', 0)

            # Compute deal score (0–100)
            deal_score = compute_deal_score(price_val, rating_val, df)

            # Generate price history
            price_history = generate_price_history(price_val) if pd.notna(price_val) else []
            avg_hist_price = sum(h['price'] for h in price_history[:-1]) / max(len(price_history) - 1, 1)
            savings_vs_avg = max(0, int(avg_hist_price - price_val))

            deals.append({
                'title': row.get('Title', 'N/A'),
                'price': f"₹{int(price_val):,}" if pd.notna(price_val) else 'N/A',
                'price_num': int(price_val) if pd.notna(price_val) else 0,
                'rating': f"{rating_val:.1f}" if pd.notna(rating_val) else 'N/A',
                'rating_num': float(rating_val) if pd.notna(rating_val) else 0,
                'url': url,
                'source': row.get('Source', 'N/A'),
                'deal_score': deal_score,
                'savings_vs_avg': savings_vs_avg,
                'price_history': price_history,
                'rank': idx + 1,
            })

        # Sort
        if sort_by == 'price_asc':
            deals.sort(key=lambda x: x['price_num'])
        elif sort_by == 'price_desc':
            deals.sort(key=lambda x: x['price_num'], reverse=True)
        elif sort_by == 'rating':
            deals.sort(key=lambda x: x['rating_num'], reverse=True)
        else:
            deals.sort(key=lambda x: x['deal_score'], reverse=True)

        # Stats for the summary bar
        prices = [d['price_num'] for d in deals if d['price_num'] > 0]
        stats = {
            'count': len(deals),
            'lowest_price': f"₹{min(prices):,}" if prices else 'N/A',
            'highest_price': f"₹{max(prices):,}" if prices else 'N/A',
            'avg_price': f"₹{int(sum(prices)/len(prices)):,}" if prices else 'N/A',
            'sources': list(set(d['source'] for d in deals)),
            'best_deal_title': deals[0]['title'][:40] + '…' if deals else '',
            'cached': use_cache and is_cache_fresh(product),
        }

        # Load plot
        plot_json = None
        plot_file = get_product_plot(product)
        if os.path.exists(plot_file):
            try:
                with open(plot_file, 'r', encoding='utf-8') as f:
                    plot_json = f.read()
            except Exception as e:
                print(f"Warning: Could not load plot: {e}")

        # Load all products for comparison table
        all_products = []
        if os.path.exists(combined_csv):
            try:
                df_all = pd.read_csv(combined_csv)
                df_all = df_all.dropna(subset=['Price_num']).head(20)
                for _, row in df_all.iterrows():
                    all_products.append({
                        'title': str(row.get('Title', ''))[:60],
                        'price': int(row.get('Price_num', 0)),
                        'rating': float(row.get('Rating_num', 0)) if pd.notna(row.get('Rating_num')) else 0,
                        'source': row.get('Source', '')
                    })
            except:
                pass

        return render_template('results.html', product=product, deals=deals,
                               plot_json=plot_json, websites=websites, error=None,
                               stats=stats, all_products=all_products,
                               sort_by=sort_by, budget_max=budget_max)

    except subprocess.TimeoutExpired:
        return render_template('results.html', product=product, deals=[], plot_json=None,
                               websites=websites, stats={}, all_products=[],
                               error="Scraping took too long. Please try again.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('results.html', product=product, deals=[], plot_json=None,
                               websites=websites, stats={}, all_products=[],
                               error=f"An error occurred: {str(e)}")


def compute_deal_score(price, rating, df):
    """Compute a 0–100 deal score based on price percentile and rating."""
    try:
        prices = df['Price_num'].dropna()
        if len(prices) == 0:
            return 50
        # Lower price = better, rating also helps
        price_pct = 1 - (price - prices.min()) / max(prices.max() - prices.min(), 1)
        rating_score = (float(rating) / 5.0) if pd.notna(rating) else 0.5
        score = (price_pct * 0.6 + rating_score * 0.4) * 100
        return round(score, 1)
    except:
        return 50.0


@app.route('/api/price-history/<path:product>')
def price_history_api(product):
    """Return simulated price history for a product."""
    base_price = request.args.get('price', 10000, type=int)
    history = generate_price_history(base_price, days=30)
    return jsonify(history)


@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    return jsonify(load_watchlist())


@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    data = request.get_json()
    watchlist = load_watchlist()
    # Avoid duplicates
    existing_urls = [w['url'] for w in watchlist]
    if data.get('url') not in existing_urls:
        watchlist.append({
            'title': data.get('title'),
            'price': data.get('price'),
            'url': data.get('url'),
            'source': data.get('source'),
            'added_at': datetime.now().isoformat()
        })
        save_watchlist(watchlist)
        return jsonify({'success': True, 'count': len(watchlist)})
    return jsonify({'success': False, 'message': 'Already in watchlist'})


@app.route('/api/watchlist/<int:index>', methods=['DELETE'])
def remove_from_watchlist(index):
    watchlist = load_watchlist()
    if 0 <= index < len(watchlist):
        watchlist.pop(index)
        save_watchlist(watchlist)
        return jsonify({'success': True})
    return jsonify({'success': False})


@app.route('/watchlist')
def watchlist_page():
    watchlist = load_watchlist()
    return render_template('watchlist.html', watchlist=watchlist)


@app.route('/api/compare')
def compare_api():
    """Return comparison data for multiple products."""
    products = request.args.getlist('products')
    result = {}
    for p in products:
        csv_file = get_product_csv(p)
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            if not df.empty:
                result[p] = df.to_dict(orient='records')
    return jsonify(result)


@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
