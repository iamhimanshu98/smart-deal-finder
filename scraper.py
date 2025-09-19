from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import plotly.express as px
import sys

search = sys.argv[1]  # take the first CLI argument

# Setup Chrome options
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', True)
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

service = Service("chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)
data = []

# --------------- AMAZON ------------------
print("\nScraping Amazon...")
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

    for product in products:
        title_tag = product.find("h2")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        price_tag = product.find("span", class_="a-price-whole")
        price = f"₹{price_tag.get_text(strip=True).replace(',', '')}" if price_tag else "N/A"

        rating_tag = product.find("i", class_="a-icon-star-small")
        rating = rating_tag.find("span", class_="a-icon-alt").get_text(strip=True) if rating_tag else "N/A"

        discount_tag = product.find("span", class_="a-letter-space")
        discount = discount_tag.find_next_sibling("span").get_text(strip=True) if discount_tag else "N/A"

        url_tag = product.find("a", class_="a-link-normal s-line-clamp-2 s-line-clamp-3-for-col-12 s-link-style a-text-normal")
        url = f"https://www.amazon.in{url_tag['href']}" if url_tag and url_tag.has_attr('href') else "N/A"

        data.append({
            "Title": title,
            "Price": price,
            "Rating": rating,
            "Discount": discount,
            "Source": "Amazon",
            "URL": url
        })

    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.s-pagination-next")
        if 'disabled' in next_btn.get_attribute("class"):
            break
        next_btn.click()
        time.sleep(2)
    except:
        break

# --------------- FLIPKART ------------------
print("\nScraping Flipkart...")

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

        data.append({
            "Title": title,
            "Price": price,
            "Rating": rating,
            "Discount": offer,
            "Source": "Flipkart",
            "URL": url
        })

def extract_small_structure():
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
                url = f"https://www.flipkart.com{url_tag.get_attribute('href')}"
            except:
                url = "N/A"

            data.append({
                "Title": title,
                "Price": price,
                "Rating": rating,
                "Discount": offer,
                "Source": "Flipkart",
                "URL": url
            })

driver.get("https://www.flipkart.com/")
time.sleep(2)
try:
    driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click()
except:
    pass

for page in range(1, page_limit + 1):
    print(f"[Flipkart] Page {page}")
    driver.get(base_url.format(page))
    time.sleep(2)
    scroll_to_bottom()
    extract_big_structure()
    extract_small_structure()

# ---------- Save to CSV ----------
driver.quit()
df = pd.DataFrame(data)
filename = f"{search.replace(' ', '_')}_combined_products.csv"
df.to_csv(filename, index=False, encoding='utf-8-sig')
print(f"\nScraping completed. Data saved to: {filename}")

# ---------- Model Training & Top 5 Deals ----------
import re
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

df = pd.read_csv(filename)

# Clean Price
df["Price_num"] = (
    df["Price"]
    .str.replace("₹", "")
    .str.replace(",", "")
    .str.strip()
    .replace("N/A", None)
    .astype(float)
)

# Clean Discount
df["Discount_pct"] = (
    df["Discount"]
    .str.extract(r"(\d+)%")
    .astype(float)
)

# Clean Rating
df["Rating_num"] = (
    df["Rating"]
    .str.extract(r"(\d+\.?\d*)")
    .astype(float)
)

# Drop rows with missing essentials
df_clean = df.dropna(subset=["Price_num", "Discount_pct", "Rating_num"]).copy()

# Filter: High ratings only
df_clean = df_clean[df_clean["Rating_num"] >= 4.5]

# Filter: Remove unrealistic low price
MIN_PRICE = 5000
df_clean = df_clean[df_clean["Price_num"] >= MIN_PRICE]

# Filter: Remove outliers by unwanted keywords
unwanted_keywords = [
    "cover", "case", "protector", "charger", "adapter",
    "cable", "screen guard", "back cover", "tempered glass"
]
pattern = '|'.join(unwanted_keywords)
mask = ~df_clean["Title"].str.lower().str.contains(pattern)
df_clean = df_clean[mask]

# Invert price for "best deal" scoring
df_clean["Price_inverted"] = df_clean["Price_num"].max() - df_clean["Price_num"]

# Prepare features for KNN
features = df_clean[["Price_inverted", "Discount_pct", "Rating_num"]].values

# Standardize
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Ideal deal: max inverted price, max discount, max rating
ideal_point = [[
    df_clean["Price_inverted"].max(),
    df_clean["Discount_pct"].max(),
    df_clean["Rating_num"].max()
]]
ideal_point_scaled = scaler.transform(ideal_point)

# KNN for top 5
knn = NearestNeighbors(n_neighbors=5, metric="euclidean")
knn.fit(features_scaled)
distances, indices = knn.kneighbors(ideal_point_scaled)

# Get top 5
top5 = df_clean.iloc[indices[0]]

print("\nTop 5 KNN Smart Deals (Filtered & Cleaned):")
print(top5[["Title", "URL", "Price_num", "Rating_num"]])

top5[["Title", "URL", "Price_num", "Rating_num"]].to_csv("Top_5_KNN_Cleaned_Deals.csv", index=False)
print("Saved to Top_5_KNN_Cleaned_Deals.csv")

# Add a column to flag top 5
df_clean["Is_Top5"] = False
df_clean.loc[top5.index, "Is_Top5"] = True

# 3D scatter plot
fig = px.scatter_3d(
    df_clean,
    x="Price_num",
    y="Discount_pct",
    z="Rating_num",
    color="Is_Top5",
    symbol="Is_Top5",
    hover_data=["Title", "Price_num", "Discount_pct", "Rating_num", "URL"],
    labels={
        "Price_num": "Price (₹)",
        "Discount_pct": "Discount (%)",
        "Rating_num": "Rating"
    },
    title="Product Deals: Cleaned vs Top 5 Best Picks"
)

fig.update_traces(marker=dict(size=5))
fig.update_layout(legend_title_text="Is Top 5 Deal?")

fig.write_json("static/plotly_graph.json")
top5[["Title", "URL", "Price_num", "Rating_num"]].to_csv("static/Top_5_KNN_Cleaned_Deals.csv", index=False)
fig.write_json("static/plotly_graph.json")