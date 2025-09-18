# Smart Deal Finder

Smart Deal Finder is a web‑scraping and recommendation tool designed to fetch product details from multiple e‑commerce websites and suggest the best available deals based on user preferences.

---

## 🚀 Features

- Automated web scraper to collect product details such as name, price, ratings, and links.
- Data cleaning and aggregation into CSV files for analysis.
- Recommendation engine using _KNN_ to identify top‑5 best deals.
- Product comparison across different brands and models.
- Lightweight web UI (Flask or similar framework) to present deals to end users.

---

## 📂 Project Structure

```
smart-deal-finder/
├── app.py                      # Web server / main application
├── scraper.py                  # Web scraping logic
├── static/                     # CSS, images, and client‑side assets
├── templates/                  # HTML templates for UI
├── *.csv                       # Scraped & cleaned product datasets
├── Top_5_KNN_Cleaned_Deals.csv # Example recommendation output
├── requirements.txt            # Python dependencies
└── chromedriver.exe            # WebDriver for Chrome scraping
```

---

## ⚙️ Installation & Setup

1. Install Python 3.x

2. Clone the repository:

   ```bash
   git clone https://github.com/iamhimanshu98/smart-deal-finder.git
   cd smart-deal-finder
   ```

3. (Optional) Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / macOS
   .\venv\Scripts\activate    # Windows
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Ensure that the installed version of Chrome matches the bundled `chromedriver.exe`. Update the path in the code if needed.

---

## ▶️ Usage

- Run the scraper to fetch product data:

  ```bash
  python scraper.py
  ```

- After scraping, launch the web application:

  ```bash
  python app.py
  ```

- Open your browser at `http://localhost:5000` to explore the top deals.

---

## 🔧 Configuration

- Update target URLs or categories directly in the scraper script.
- Adjust the KNN parameters or similarity metrics for different recommendation logic.
- Modify CSV output file names or storage paths if required.

---

## 🧪 Contributing

- Report bugs in the Issues section.
- Contributions are welcome via Pull Requests.
- Ensure code readability and add comments, especially for scraping logic.

---

## ⚠️ Disclaimer

- Web scraping may be subject to legal and ethical considerations. Always respect website `robots.txt` and terms of service.
- Scraper reliability depends on the website structure; changes in site layout may break functionality.
- Implement rate limiting or delays to avoid IP blocking.

---

## 📄 License

This project is licensed under _\[Insert License]_ (e.g., MIT / Apache / GPL).

---

## 📬 Contact

For questions, suggestions, or collaboration:

- **Author**: Himanshu
- **GitHub**: [iamhimanshu98](https://github.com/iamhimanshu98)
