from flask import Flask, render_template, request
import subprocess
import pandas as pd
import plotly.express as px

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    product = request.form['product'].strip()

    # ✅ 1️⃣ Run your scraper
    subprocess.run(['python', 'scraper.py', product])

    # ✅ 2️⃣ Load top 5 deals from CSV
    df = pd.read_csv('Top_5_KNN_Cleaned_Deals.csv')
    deals = df.to_dict(orient='records')

    # ✅ 3️⃣ Create Plotly 3D scatter plot
    fig = px.scatter(
        df,
        x="Price_num",
        y="Rating_num",
        color="Title",
        hover_data=["Title", "URL", "Price_num", "Rating_num"],
        labels={
            "Price_num": "Price (₹)",
            "Rating_num": "Rating"
        },
        title=f"Deals for {product}"
    )
    fig_json = fig.to_json()

    # ✅ 4️⃣ Render results page
    return render_template('results.html',
                           product=product,
                           deals=deals,
                           plot_json=fig_json)

if __name__ == '__main__':
    app.run(debug=True)






