# 📈 Market Intelligence Dashboard

A live market intelligence dashboard built with Streamlit that tracks real-time crypto and stock prices, plots historical trends, and forecasts BTC price using Linear Regression.

**Live Demo:** https://appdashboard-d436rt7ev7v3p6tjzdoaqs.streamlit.app/

---

## Features

- **Live price cards** for BTC, ETH, SOL, DOGE, AAPL, and TSLA with % change from last reading
- **Historical line charts** with volatility bars for each asset
- **Normalised comparison chart** — compare any combination of assets on the same scale regardless of price difference
- **BTC price prediction** using Linear Regression with adjustable forecast horizon
- **Auto-refreshes every 30 seconds** — no manual reload needed
- **Data collected every 2 minutes** via a background scheduler embedded in the app

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend & server | Streamlit |
| Crypto prices | CoinGecko API (free tier, no key needed) |
| Stock prices | yFinance |
| Charts | Plotly |
| Background scheduling | APScheduler |
| ML prediction | scikit-learn (Linear Regression) |
| Data storage | CSV (local, rebuilt on each deployment) |
| Deployment | Streamlit Cloud |

---

## Project Structure

```
├── app.py                  # Main Streamlit app + scheduler bootstrap
├── modules/
│   ├── data_fetcher.py     # Fetches live prices from CoinGecko and yFinance
│   └── analysis.py         # CSV persistence + Plotly chart builders
├── data/                   # Auto-created at runtime, gitignored
│   └── prices.csv
├── .streamlit/
│   └── config.toml         # Dark theme config
└── requirements.txt
```

---

## How It Works

### The scheduling problem
Streamlit reruns your entire script from top to bottom on every interaction or timer tick. You can't just start a background job at the top of the file — it would spawn a new scheduler on every rerun.

The fix: `st.session_state` persists across reruns within a session. We use it as a "scheduler already started" flag so APScheduler only initialises once per browser session, running in a background thread while Streamlit handles the UI on the main thread.

### Why CSV and not a database
CSV works fine for a single-developer deployment. The tradeoff is that Streamlit Cloud resets the filesystem on every restart, so collected history rebuilds from zero after inactivity. The app handles this gracefully — price cards work immediately, charts fill in over the first few minutes.

### Auto-refresh
Streamlit has no built-in timer. The pattern used here: render all UI, `time.sleep(1)`, call `st.rerun()` — creating a 1-second countdown loop. Every 30 seconds the rerun re-reads the CSV and redraws all charts with the latest data.

---

## Run Locally

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`. The first data point is collected immediately on startup, with new rows added every 2 minutes.

---

## Future Improvements

- [ ] PostgreSQL for persistent storage across restarts
- [ ] More assets (top 10 crypto, S&P 500 components)
- [ ] Candlestick charts using OHLC data
- [ ] Email/Telegram alerts when price crosses a threshold
- [ ] Better ML model (LSTM or Prophet instead of Linear Regression)