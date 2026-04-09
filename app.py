from flask import Flask, render_template, request, jsonify
import subprocess
import pandas as pd
import plotly.express as px
import os
import json

app = Flask(__name__)

# Ensure static folder exists
os.makedirs("static", exist_ok=True)

def get_product_csv(product):
    """Generate the CSV filename for a given product search."""
    product_filename = product.replace(" ", "_").lower()
    return os.path.join("static", f"top5_{product_filename}.csv")

def get_product_plot(product):
    """Generate the plot filename for a given product search."""
    product_filename = product.replace(" ", "_").lower()
    return os.path.join("static", f"top5_{product_filename}_plot.json")

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle product search and return results."""
    product = ""
    websites = []
    
    try:
        product = request.form['product'].strip()
        websites = request.form.getlist('websites')
        
        if not product:
            return render_template('results.html', 
                                 product="", 
                                 deals=[], 
                                 plot_json=None,
                                 websites=[],
                                 error="Please enter a product name.")
        
        if len(websites) < 2:
            return render_template('results.html', 
                                 product=product, 
                                 deals=[], 
                                 plot_json=None,
                                 websites=websites,
                                 error="Please select at least 2 websites.")
        
        print(f"\n=== Searching for: {product} ===")
        print(f"Selected websites: {', '.join(websites)}")
        
        print("Running scraper...")
        websites_str = ",".join(websites)
        result = subprocess.run(
            ['python', 'scraper.py', product, websites_str],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        # Print both stdout and stderr for debugging
        print("--- SCRAPER OUTPUT ---")
        print(result.stdout)
        if result.stderr:
            print("--- SCRAPER ERRORS ---")
            print(result.stderr)
        print("--- END OUTPUT ---")
        
        if result.returncode != 0:
            # Get full error message from stderr
            error_msg = result.stderr.strip() if result.stderr else "Unknown error occurred"
            print(f"[ERROR] Scraper failed with return code {result.returncode}")
            print(f"[ERROR] Error message: {error_msg}")
            
            return render_template('results.html', 
                                 product=product, 
                                 deals=[], 
                                 plot_json=None,
                                 websites=websites,
                                 error=f"Scraping failed: {error_msg[-500:]}")
        
        print("Scraper completed successfully.")
        
        csv_file = get_product_csv(product)
        
        if not os.path.exists(csv_file):
            return render_template('results.html', 
                                 product=product, 
                                 deals=[], 
                                 plot_json=None,
                                 websites=websites,
                                 error=f"No results found for '{product}'. Try a different search.")
        
        df = pd.read_csv(csv_file)
        
        if df.empty:
            return render_template('results.html', 
                                 product=product, 
                                 deals=[], 
                                 plot_json=None,
                                 websites=websites,
                                 error=f"No deals found for '{product}'.")
        
        deals = []
        for idx, row in df.iterrows():
            url = str(row.get('URL', '#'))
            
            # Validate and fix URL
            if url and url != 'N/A' and url.startswith('http'):
                # URL is valid, keep it
                pass
            else:
                # Invalid URL, create search link instead
                product_name = row.get('Title', 'Product')
                if row.get('Source') == 'Amazon':
                    url = f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}"
                elif row.get('Source') == 'Flipkart':
                    url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '+')}"
                else:
                    url = f"https://www.croma.com/search?q={product_name.replace(' ', '+')}"
            
            deals.append({
                'title': row.get('Title', 'N/A'),
                'price': f"Rs.{row.get('Price_num', 0):.0f}" if pd.notna(row.get('Price_num')) else 'N/A',
                'rating': f"{row.get('Rating_num', 0):.1f}" if pd.notna(row.get('Rating_num')) else 'N/A',
                'url': url,
                'source': row.get('Source', 'N/A')
            })

        
        print(f"Found {len(deals)} top deals.")
        
        plot_json = None
        plot_file = get_product_plot(product)
        if os.path.exists(plot_file):
            try:
                with open(plot_file, 'r', encoding='utf-8') as f:
                    plot_json = f.read()
            except Exception as e:
                print(f"Warning: Could not load plot: {e}")
        
        return render_template('results.html',
                             product=product,
                             deals=deals,
                             plot_json=plot_json,
                             websites=websites,
                             error=None)
    
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] Scraping took too long")
        return render_template('results.html', 
                             product=product, 
                             deals=[], 
                             plot_json=None,
                             websites=websites,
                             error="Scraping took too long (over 10 minutes). Please try again with a simpler search.")
    
    except Exception as e:
        print(f"[EXCEPTION] {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('results.html', 
                             product=product, 
                             deals=[], 
                             plot_json=None,
                             websites=websites,
                             error=f"An error occurred: {str(e)}")

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, threaded=True)



"""
wgrolg"""