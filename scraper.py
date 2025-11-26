from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import plotly.express as px
import sys
import os

# Take search term and websites from CLI arguments
search = sys.argv[1]
websites_str = sys.argv[2] if len(sys.argv) > 2 else "amazon,flipkart"
selected_websites = [w.strip().lower() for w in websites_str.split(",")]

print(f"\n{'='*50}")
print(f"Searching for: {search}")
print(f"Websites: {', '.join(selected_websites)}")
print(f"{'='*50}")

# Create static folder if it doesn't exist
os.makedirs("static", exist_ok=True)

# Setup Chrome options
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

def fix_url(raw, base):
    if not raw:
        return "N/A"

    raw = raw.strip()

    # Fix missing colon cases like "https//"
    raw = raw.replace("https//", "https://").replace("http//", "http://")

    # If already absolute URL
    if raw.startswith("http"):
        return raw

    # If URL begins with "/", example: /apple-iphone...
    if raw.startswith("/"):
        return base + raw

    # If URL starts with www.amazon.in or www.flipkart.com
    if raw.startswith("www."):
        return "https://" + raw

    # Last fallback
    return base + "/" + raw.lstrip("/")


# Use webdriver-manager to auto-download correct ChromeDriver
try:
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
except Exception as e:
    print(f"Error initializing Chrome: {e}")
    sys.exit(1)

data = []

# --------------- AMAZON ------------------
if 'amazon' in selected_websites:
    print("\n[AMAZON] Starting scrape...")
    try:
        driver.get("https://www.amazon.in/")
        time.sleep(2)
        
        search_box = driver.find_element(By.ID, "twotabsearchtextbox")
        search_box.clear()
        search_box.send_keys(search)
        driver.find_element(By.ID, "nav-search-submit-button").click()
        time.sleep(2)
        
        for page in range(1, 3):
            print(f"[Amazon] Page {page}")
            soup = BeautifulSoup(driver.page_source, "html.parser")
            products = soup.find_all("div", {"data-component-type": "s-search-result"})
            
            print(f"  Found {len(products)} products on page {page}")
            
            for product in products:
                try:
                    title_tag = product.find("h2")
                    title = title_tag.get_text(strip=True) if title_tag else "N/A"
                    
                    price_tag = product.find("span", class_="a-price-whole")
                    price = f"Rs.{price_tag.get_text(strip=True).replace(',', '')}" if price_tag else "N/A"
                    
                    rating_tag = product.find("i", class_="a-icon-star-small")
                    rating = rating_tag.find("span", class_="a-icon-alt").get_text(strip=True) if rating_tag else "N/A"
                    
                    discount_tag = product.find("span", class_="a-letter-space")
                    discount = discount_tag.find_next_sibling("span").get_text(strip=True) if discount_tag else "N/A"
                    
                    url_tag = product.find("a", class_="a-link-normal s-line-clamp-2 s-line-clamp-3-for-col-12 s-link-style a-text-normal")
                    href = url_tag['href'] if url_tag and url_tag.has_attr('href') else None 
                    url = fix_url(href, "https://www.amazon.in")

                    
                    if title != "N/A":
                        data.append({
                            "Title": title,
                            "Price": price,
                            "Rating": rating,
                            "Discount": discount,
                            "Source": "Amazon",
                            "URL": url
                        })
                except Exception as e:
                    continue
            
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "a.s-pagination-next")
                if 'disabled' in next_btn.get_attribute("class"):
                    print(f"  No more pages for Amazon")
                    break
                next_btn.click()
                time.sleep(2)
            except:
                print(f"  Reached end of Amazon pages")
                break
        
        amazon_count = len([d for d in data if d['Source'] == 'Amazon'])
        print(f"[OK] Amazon scraping completed. Total products: {amazon_count}")
    except Exception as e:
        print(f"[ERROR] Amazon scraping failed: {e}")

# --------------- FLIPKART ------------------
if 'flipkart' in selected_websites:
    print("\n[FLIPKART] Starting scrape...")
    try:
        base_url = f"https://www.flipkart.com/search?q={search}&page={{}}"
        page_limit = 3
        
        def scroll_to_bottom():
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        
        def extract_big_structure():
            count = 0
            try:
                cards = driver.find_elements(By.CLASS_NAME, "tUxRFH")
                for card in cards:
                    try:
                        title = card.find_element(By.CLASS_NAME, "KzDlHZ").text.strip()
                    except:
                        title = "N/A"
                    try:
                        rating_raw = card.find_element(By.CLASS_NAME, "_5OesEi").find_element(By.CLASS_NAME, "XQDdHH").text.strip()
                        rating = f"{rating_raw} out of 5"
                    except:
                        rating = "N/A"
                    try:
                        price = card.find_element(By.CLASS_NAME, "Nx9bqj").text.strip()
                    except:
                        price = "N/A"
                    try:
                        offer_raw = card.find_element(By.CLASS_NAME, "UkUFwK").find_element(By.TAG_NAME, "span").text.strip()
                        offer = f"({offer_raw})"
                    except:
                        offer = "N/A"
                    try:
                        url_tag = card.find_element(By.CLASS_NAME, "CGtC98")
                        url = f"https://www.flipkart.com{url_tag.get_attribute('href')}"
                    except:
                        url = "N/A"
                    
                    if title != "N/A":
                        data.append({
                            "Title": title,
                            "Price": price,
                            "Rating": rating,
                            "Discount": offer,
                            "Source": "Flipkart",
                            "URL": url
                        })
                        count += 1
            except Exception as e:
                print(f"  Error in big structure extraction: {e}")
            
            return count
        
        def extract_small_structure():
            count = 0
            try:
                containers = driver.find_elements(By.CLASS_NAME, "_75nlfW")
                for container in containers:
                    cards = container.find_elements(By.XPATH, './/div[@style="width: 25%;"]')
                    for card in cards:
                        try:
                            title = card.find_element(By.CLASS_NAME, "wjcEIp").text.strip()
                        except:
                            title = "N/A"
                        try:
                            rating_raw = card.find_element(By.CLASS_NAME, "_5OesEi").find_element(By.CLASS_NAME, "XQDdHH").text.strip()
                            rating = f"{rating_raw} out of 5"
                        except:
                            rating = "N/A"
                        try:
                            price = card.find_element(By.CLASS_NAME, "hl05eU").find_element(By.CLASS_NAME, "Nx9bqj").text.strip()
                        except:
                            price = "N/A"
                        try:
                            offer_raw = card.find_element(By.CLASS_NAME, "hl05eU").find_element(By.CLASS_NAME, "UkUFwK").find_element(By.TAG_NAME, "span").text.strip()
                            offer = f"({offer_raw})"
                        except:
                            offer = "N/A"
                        try:
                            url_tag = card.find_element(By.CLASS_NAME, "CGtC98")
                            raw_href = url_tag.get_attribute('href')
                            url = fix_url(raw_href, "")

                        except:
                            url = "N/A"
                        
                        if title != "N/A":
                            data.append({
                                "Title": title,
                                "Price": price,
                                "Rating": rating,
                                "Discount": offer,
                                "Source": "Flipkart",
                                "URL": url
                            })
                            count += 1
            except Exception as e:
                print(f"  Error in small structure extraction: {e}")
            
            return count
        
        driver.get("https://www.flipkart.com/")
        time.sleep(2)
        try:
            driver.find_element(By.XPATH, "//button[contains(text(), 'X')]").click()
        except:
            pass
        
        for page in range(1, page_limit + 1):
            print(f"[Flipkart] Page {page}")
            driver.get(base_url.format(page))
            time.sleep(2)
            scroll_to_bottom()
            count1 = extract_big_structure()
            count2 = extract_small_structure()
            print(f"  Found {count1 + count2} products on page {page}")
        
        flipkart_total = len([d for d in data if d['Source'] == 'Flipkart'])
        print(f"[OK] Flipkart scraping completed. Total products: {flipkart_total}")
    except Exception as e:
        print(f"[ERROR] Flipkart scraping failed: {e}")

# --------------- CROMA (Optional) ------------------
if 'croma' in selected_websites:
    print("\n[CROMA] Starting scrape...")
    try:
        croma_url = f"https://www.croma.com/search?q={search}"
        driver.get(croma_url)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        products = soup.find_all("div", class_="productCardImg")
        
        print(f"  Found {len(products)} products on Croma")
        
        count = 0
        for product in products:
            try:
                title_tag = product.find("h3") or product.find("p")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                
                price_tag = product.find("span", class_="sellingPrice")
                price = price_tag.get_text(strip=True) if price_tag else "N/A"
                
                rating_tag = product.find("span", class_="ratingCount")
                rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"
                
                discount_tag = product.find("span", class_="discountLabel")
                discount = discount_tag.get_text(strip=True) if discount_tag else "N/A"
                
                url_tag = product.find("a")
                href = url_tag['href'] if url_tag and url_tag.has_attr('href') else None
                url = fix_url(href, "https://www.croma.com")

                
                if title != "N/A":
                    data.append({
                        "Title": title,
                        "Price": price,
                        "Rating": rating,
                        "Discount": discount,
                        "Source": "Croma",
                        "URL": url
                    })
                    count += 1
            except Exception as e:
                continue
        
        croma_total = len([d for d in data if d['Source'] == 'Croma'])
        print(f"[OK] Croma scraping completed. Total products: {croma_total}")
    except Exception as e:
        print(f"[ERROR] Croma scraping failed: {e}")

# ---------- Close driver ----------
print("\nClosing browser...")
driver.quit()

# ---------- Save combined products CSV ----------
print(f"\nTotal products collected: {len(data)}")

if len(data) == 0:
    print("ERROR: No products were scraped!")
    sys.exit(1)

df = pd.DataFrame(data)
combined_filename = f"{search.replace(' ', '_')}_combined_products.csv"
combined_filepath = os.path.join("static", combined_filename)
df.to_csv(combined_filepath, index=False, encoding='utf-8-sig')
print(f"[OK] Data saved to: {combined_filepath}")

# ---------- Model Training & Top 5 Deals ----------
print("\n" + "="*50)
print("PROCESSING DATA WITH KNN ALGORITHM")
print("="*50)

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.neighbors import NearestNeighbors
    
    # Read the combined products
    df = pd.read_csv(combined_filepath)
    print(f"[OK] Loaded {len(df)} products from CSV")
    
    # DEBUG: Print first few rows to understand data format
    print("\n--- DEBUG: First 3 rows of raw data ---")
    for idx, row in df.head(3).iterrows():
        print(f"Row {idx}:")
        print(f"  Price: '{row['Price']}' (type: {type(row['Price'])})")
        print(f"  Discount: '{row['Discount']}' (type: {type(row['Discount'])})")
        print(f"  Rating: '{row['Rating']}' (type: {type(row['Rating'])})")
    print("--- END DEBUG ---\n")
    
    # Convert all relevant columns to string first
    df["Price"] = df["Price"].astype(str)
    df["Discount"] = df["Discount"].astype(str)
    df["Rating"] = df["Rating"].astype(str)
    
    # Clean Price - handle malformed data
    def extract_price(price_str):
        try:
            # Remove all non-digit characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', str(price_str))
            # Handle multiple decimals like ".1798." -> keep only first decimal
            if cleaned.count('.') > 1:
                parts = cleaned.split('.')
                cleaned = parts[0] + '.' + parts[1]  # Keep first decimal only
            if cleaned and cleaned != '.' and cleaned != '':
                val = float(cleaned)
                if val > 0:
                    return val
        except:
            pass
        return None
    
    df["Price_num"] = df["Price"].apply(extract_price)
    
    # Clean Discount - extract percentage number
    def extract_discount(discount_str):
        try:
            match = re.search(r'(\d+)', str(discount_str))
            if match:
                return float(match.group(1))
        except:
            pass
        return 0  # Default to 0 if no discount found
    
    df["Discount_pct"] = df["Discount"].apply(extract_discount)
    
    # Clean Rating - extract rating number
    def extract_rating(rating_str):
        try:
            if str(rating_str) == 'nan' or str(rating_str) == 'N/A':
                return None
            match = re.search(r'(\d+\.?\d*)', str(rating_str))
            if match:
                val = float(match.group(1))
                if 0 < val <= 10:  # Valid rating range
                    return val
        except:
            pass
        return None
    
    df["Rating_num"] = df["Rating"].apply(extract_rating)
    
    print(f"[DEBUG] After extraction:")
    print(f"  Price_num: {df['Price_num'].notna().sum()} non-null values")
    print(f"  Discount_pct: {df['Discount_pct'].notna().sum()} non-null values")
    print(f"  Rating_num: {df['Rating_num'].notna().sum()} non-null values")
    print(f"  Sample Price_num values: {df['Price_num'].dropna().head(3).tolist()}")
    print(f"  Sample Discount_pct values: {df['Discount_pct'].head(3).tolist()}")
    print(f"  Sample Rating_num values: {df['Rating_num'].dropna().head(3).tolist()}")
    
    # Since ratings are missing, let's assign default ratings based on source
    # Amazon and Flipkart usually have good products, so assign default 4.5
    df.loc[df["Rating_num"].isna() & (df["Source"] == "Amazon"), "Rating_num"] = 4.5
    df.loc[df["Rating_num"].isna() & (df["Source"] == "Flipkart"), "Rating_num"] = 4.3
    df.loc[df["Rating_num"].isna() & (df["Source"] == "Croma"), "Rating_num"] = 4.4
    
    print(f"[OK] After assigning default ratings:")
    print(f"  Rating_num: {df['Rating_num'].notna().sum()} non-null values")
    
    # Drop rows with missing Price
    df_clean = df.dropna(subset=["Price_num"]).copy()
    print(f"[OK] After removing null prices: {len(df_clean)} valid products")
    
    if len(df_clean) == 0:
        print("ERROR: No valid products after cleaning.")
        print("\nDEBUG: Full data sample:")
        print(df[["Title", "Price", "Discount", "Rating"]].head(10))
        sys.exit(1)
    
    # Filter: Minimum rating
    df_clean = df_clean[df_clean["Rating_num"] >= 3.0]
    print(f"[OK] After rating filter (>=3.0): {len(df_clean)} products")
    
    # Filter: Remove unrealistic low prices
    MIN_PRICE = 1000  # For phones/electronics
    df_clean = df_clean[df_clean["Price_num"] >= MIN_PRICE]
    print(f"[OK] After price filter (>=Rs.{MIN_PRICE}): {len(df_clean)} products")
    
    # Filter: Remove unrealistic high prices (over 500k)
    MAX_PRICE = 500000
    df_clean = df_clean[df_clean["Price_num"] <= MAX_PRICE]
    print(f"[OK] After max price filter (<=Rs.{MAX_PRICE}): {len(df_clean)} products")
    
    # Filter: Remove outliers by unwanted keywords
    unwanted_keywords = [
        "cover", "case", "protector", "charger", "adapter",
        "cable", "screen guard", "back cover", "tempered glass", "film",
        "stand", "mount", "holder"
    ]
    pattern = '|'.join(unwanted_keywords)
    mask = ~df_clean["Title"].str.lower().str.contains(pattern, na=False)
    df_clean = df_clean[mask]
    print(f"[OK] After keyword filter: {len(df_clean)} products")
    
    if len(df_clean) == 0:
        print("ERROR: No products after filtering.")
        print(f"Total before keyword filter: {len(df)}")
        sys.exit(1)
    
    # Remove duplicates based on title
    df_clean = df_clean.drop_duplicates(subset=["Title"], keep='first')
    print(f"[OK] After removing duplicates: {len(df_clean)} products")
    
    # Invert price for "best deal" scoring
    df_clean["Price_inverted"] = df_clean["Price_num"].max() - df_clean["Price_num"]
    
    # Prepare features for KNN
    features = df_clean[["Price_inverted", "Discount_pct", "Rating_num"]].values
    
    # Standardize
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    print(f"[OK] Features scaled and standardized")
    
    # Ideal deal: max inverted price, max discount, max rating
    ideal_point = [[
        df_clean["Price_inverted"].max(),
        df_clean["Discount_pct"].max(),
        df_clean["Rating_num"].max()
    ]]
    ideal_point_scaled = scaler.transform(ideal_point)
    
    # KNN for top 5
    n_neighbors = min(5, len(df_clean))
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean")
    knn.fit(features_scaled)
    distances, indices = knn.kneighbors(ideal_point_scaled)
    
    # Get top N
    top_n = df_clean.iloc[indices[0]]
    
    print(f"\n{'='*50}")
    print(f"TOP {n_neighbors} KNN SMART DEALS")
    print(f"{'='*50}")
    for idx, (i, row) in enumerate(top_n.iterrows(), 1):
        print(f"{idx}. {row['Title'][:50]}")
        print(f"   Price: Rs.{row['Price_num']:.0f} | Rating: {row['Rating_num']:.1f} | Discount: {row['Discount_pct']:.0f}% | Source: {row['Source']}")
    
    # Save top deals to CSV with dynamic filename
    top_deals_filename = f"top5_{search.replace(' ', '_').lower()}.csv"
    top_deals_filepath = os.path.join("static", top_deals_filename)
    top_n[["Title", "URL", "Price_num", "Rating_num", "Source"]].to_csv(top_deals_filepath, index=False)
    print(f"\n[OK] Top deals saved to {top_deals_filepath}")
    
    # Create 3D visualization
    try:
        df_clean["Is_Top5"] = False
        df_clean.loc[top_n.index, "Is_Top5"] = True
        
        fig = px.scatter_3d(
            df_clean,
            x="Price_num",
            y="Discount_pct",
            z="Rating_num",
            color="Is_Top5",
            symbol="Is_Top5",
            hover_data=["Title", "Price_num", "Discount_pct", "Rating_num", "Source", "URL"],
            labels={
                "Price_num": "Price (Rs.)",
                "Discount_pct": "Discount (%)",
                "Rating_num": "Rating"
            },
            title=f"Product Analysis: {search} - Top 5 Deals Highlighted",
            color_discrete_map={True: "#10b981", False: "#e5e7eb"}
        )
        
        fig.update_traces(marker=dict(size=5))
        fig.update_layout(legend_title_text="Top 5 Deal?")
        
        plot_filename = f"top5_{search.replace(' ', '_').lower()}_plot.json"
        plot_filepath = os.path.join("static", plot_filename)
        fig.write_json(plot_filepath)
        print(f"[OK] Visualization saved to {plot_filepath}")
    except Exception as e:
        print(f"[WARN] Could not create visualization: {e}")

    print(f"\n{'='*50}")
    print("SCRAPING AND PROCESSING COMPLETE!")
    print(f"{'='*50}\n")

except Exception as e:
    print(f"ERROR in model training: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
