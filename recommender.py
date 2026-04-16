"""
recommender.py — Smart Deal Scoring & KNN Recommendation Engine
B.Tech Final Year Project: Smart Deal Finder

This module separates ML logic from the scraper for clean architecture.
"""

import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.neighbors import NearestNeighbors


# ─────────────────────────────────────────────────────────────
# Price / Rating / Discount Extraction
# ─────────────────────────────────────────────────────────────

def extract_price(price_str) -> float | None:
    """Extract numeric price from string like 'Rs.45,990' or '₹45990'."""
    try:
        cleaned = str(price_str).replace("Rs.", "").replace("₹", "").replace(",", "").strip()
        match = re.search(r'(\d+\.?\d*)', cleaned)
        if match:
            val = float(match.group(1))
            if 100 <= val <= 1_000_000:  # reasonable range
                return val
    except:
        pass
    return None


def extract_discount(discount_str) -> float:
    """Extract discount percentage from strings like '(20% off)' or '20%'."""
    try:
        match = re.search(r'(\d+)', str(discount_str))
        if match:
            return float(match.group(1))
    except:
        pass
    return 0.0


def extract_rating(rating_str) -> float | None:
    """Extract numeric rating from '4.3 out of 5' or '4.3'."""
    try:
        raw = str(rating_str)
        if raw in ('nan', 'N/A', '', 'None'):
            return None
        match = re.search(r'(\d+\.?\d*)', raw)
        if match:
            val = float(match.group(1))
            if 0 < val <= 10:
                return val
    except:
        pass
    return None


# ─────────────────────────────────────────────────────────────
# Cleaning Pipeline
# ─────────────────────────────────────────────────────────────

UNWANTED_KEYWORDS = [
    "cover", "case", "protector", "charger", "adapter", "cable",
    "screen guard", "back cover", "tempered glass", "film",
    "stand", "mount", "holder", "skin", "wrap", "strap", "band"
]

def clean_dataframe(df: pd.DataFrame, min_price: float = 500,
                    max_price: float = 500_000,
                    min_rating: float = 3.0) -> pd.DataFrame:
    """
    Full cleaning pipeline:
    1. Extract numeric features
    2. Fill missing ratings by source
    3. Drop invalid / outlier rows
    4. Remove accessory keywords
    5. Deduplicate by title
    """
    df = df.copy()

    # Convert to string to avoid type errors
    for col in ["Price", "Discount", "Rating"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    df["Price_num"] = df["Price"].apply(extract_price)
    df["Discount_pct"] = df["Discount"].apply(extract_discount) if "Discount" in df.columns else 0
    df["Rating_num"] = df["Rating"].apply(extract_rating) if "Rating" in df.columns else None

    # Default ratings per source
    defaults = {"Amazon": 4.2, "Flipkart": 4.0, "Croma": 4.1}
    for source, default in defaults.items():
        mask = df["Rating_num"].isna() & (df["Source"] == source)
        df.loc[mask, "Rating_num"] = default

    # Drop rows with no valid price
    df = df.dropna(subset=["Price_num"])

    # Price range filter
    df = df[(df["Price_num"] >= min_price) & (df["Price_num"] <= max_price)]

    # Rating filter
    df = df[df["Rating_num"] >= min_rating]

    # Keyword filter (removes accessories)
    pattern = '|'.join(UNWANTED_KEYWORDS)
    df = df[~df["Title"].str.lower().str.contains(pattern, na=False)]

    # Deduplication
    df = df.drop_duplicates(subset=["Title"], keep="first")

    return df.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# Deal Scoring
# ─────────────────────────────────────────────────────────────

def compute_deal_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'deal_score' column (0–100) using weighted combination:
      - Price (lower = better): 50%
      - Rating:                 30%
      - Discount:               20%
    """
    df = df.copy()
    scaler = MinMaxScaler()

    # Invert price (lower is better)
    df["price_score"] = 1 - scaler.fit_transform(df[["Price_num"]]).flatten()
    df["rating_score"] = scaler.fit_transform(df[["Rating_num"]]).flatten()
    df["discount_score"] = scaler.fit_transform(df[["Discount_pct"]]).flatten()

    df["deal_score"] = (
        df["price_score"] * 50 +
        df["rating_score"] * 30 +
        df["discount_score"] * 20
    ).round(1)

    return df


# ─────────────────────────────────────────────────────────────
# KNN Recommendation
# ─────────────────────────────────────────────────────────────

def recommend_top_n(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Apply KNN to find the top N products closest to the 'ideal deal':
    - Ideal: lowest price, highest discount, highest rating
    Returns a DataFrame of the top N rows (with deal_score column).
    """
    df = compute_deal_scores(df)

    if len(df) < n:
        n = len(df)

    # Feature matrix
    df["Price_inverted"] = df["Price_num"].max() - df["Price_num"]
    features = df[["Price_inverted", "Discount_pct", "Rating_num"]].values

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Ideal point
    ideal = [[
        df["Price_inverted"].max(),
        df["Discount_pct"].max(),
        df["Rating_num"].max()
    ]]
    ideal_scaled = scaler.transform(ideal)

    knn = NearestNeighbors(n_neighbors=n, metric="euclidean")
    knn.fit(features_scaled)
    distances, indices = knn.kneighbors(ideal_scaled)

    top_df = df.iloc[indices[0]].copy()
    top_df["knn_distance"] = distances[0]

    return top_df


# ─────────────────────────────────────────────────────────────
# Quick CLI test
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, os
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    if csv_path and os.path.exists(csv_path):
        raw = pd.read_csv(csv_path)
        cleaned = clean_dataframe(raw)
        print(f"Cleaned: {len(cleaned)} products")
        top5 = recommend_top_n(cleaned, n=5)
        print("\nTop 5 Deals:")
        for _, row in top5.iterrows():
            print(f"  [{row['deal_score']:.1f}] {row['Title'][:50]} — ₹{row['Price_num']:.0f} ({row['Source']})")
    else:
        print("Usage: python recommender.py <path_to_csv>")
