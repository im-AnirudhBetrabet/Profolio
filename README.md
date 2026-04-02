# 💠 ProFolio Command Center

**ProFolio** is a premium, automated stock portfolio dashboard tailored for the Indian stock market. It bridges your official Zerodha broker account with real-time market data to track investments, perform quantitative technical analysis, and visualize asset allocation through a modern, glassmorphic interface.

Designed with an extensible architecture, ProFolio is built not just as a visual ledger, but as a foundational dashboard ready for future Applied AI and predictive scoring integrations.

## ✨ Features
* **Automated Broker Sync:** Seamless OAuth login flow with Zerodha (Kite Connect) to fetch live portfolio holdings.
* **Smart Data Fallback Engine:** Pulls real-time market data via `yfinance`, with an automatic fallback routing from NSE (`.NS`) to BSE (`.BO`) to ensure uninterrupted data flow.
* **Premium UI/UX:** A custom-styled, minimalistic glassmorphism aesthetic featuring dynamic progress bars, Plotly treemaps, and interactive datatables.
* **Quantitative Analysis Hub:** Interactive subplots featuring price action, 20/50/200-day Simple Moving Averages (SMAs), Volume Profiling, and a 14-day RSI momentum indicator.
* **Local Caching:** Intelligently caches your portfolio locally to avoid rate limits and ensure lightning-fast dashboard loads.

---

## 🛠️ Prerequisites & Zerodha API Setup

To run this application, you will need an active Zerodha account and access to the Kite Connect API.

### 1. Acquiring Your API Credentials
Kite Connect is Zerodha's developer API suite. *Note: Zerodha charges a monthly fee (currently ₹2000/month) for API access.*

1. Go to the [Kite Connect Developer Portal](https://developers.kite.trade/) and sign up or log in.
2. Click on **Create New App**.
3. Fill in the required details (App Name, Description, etc.).
4. **CRITICAL STEP:** Set the **Redirect URL** to `http://127.0.0.1:8501/`. 
   * *Why?* Streamlit runs on port 8501 by default. ProFolio is designed to catch the authentication token directly from the URL after you log in. If this is not set correctly, the auto-sync will fail.
5. Once the app is created, copy your **API Key** and **API Secret**. You will enter these directly into the ProFolio sidebar.

---

## 🚀 Installation & Local Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/profolio.git](https://github.com/yourusername/profolio.git)
cd profolio
```

### 2. Create a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.
For windows
```commandline
python -m venv venv
venv\Scripts\activate
```
For macOS/Linux
```commandline
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```commandline
pip install -r requirements.txt
```

## 🖥️ Running the Application
Once your environment is activated and dependencies are installed, start the Streamlit server:
```commandline
streamlit run main.py
```

### Usage Flow:
1. Open the app in your browser (usually http://localhost:8501).
2. Open the sidebar and enter your Zerodha API Key and API Secret. Click Save Credentials.
3. Click the generated Login URL to authenticate with Zerodha.
4. Once authenticated, the app will catch your token, sync your live holdings, cache them locally, and unlock the command center.

⚠️ Disclaimer
This software is for educational and informational purposes only. It is not financial advice. 
Ensure you keep your API Secret secure and never commit your credentials.json or saved_portfolio.json files to public version control. Ensure they are added to your .gitignore.