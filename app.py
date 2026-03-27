
import time
import streamlit as st
from apscheduler.schedulers.background import BackgroundScheduler

from modules.data_fetcher import get_crypto_prices, get_stock_prices
from modules.analysis import save_prices, load_prices
from modules.analysis import make_price_chart, make_comparison_chart, make_btc_prediction_chart




CRYPTO_SYMS  = ["BTC", "ETH", "SOL", "DOGE"]
STOCK_SYMS   = ["AAPL", "TSLA"]
ALL_ASSETS   = CRYPTO_SYMS + STOCK_SYMS

REFRESH_SECS = 30    # How often the Streamlit display auto-refreshes
COLLECT_SECS = 120   # How often the scheduler writes a new CSV row




def collect_and_save():
    try:
        btc, eth, sol, doge = get_crypto_prices()
        aapl, tsla = get_stock_prices()

        prices = {
            "BTC": btc, "ETH": eth, "SOL": sol, "DOGE": doge,
            "AAPL": aapl, "TSLA": tsla,
        }
        save_prices(prices)

    except Exception as e:
        print(f"[Scheduler] Error collecting prices: {e}")

if "scheduler_started" not in st.session_state:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        collect_and_save,
        trigger="interval",
        seconds=COLLECT_SECS,
        id="price_collector",
        replace_existing=True,
    )
    scheduler.start()

    # Run once immediately so you don't wait 2 minutes for the first data point
    collect_and_save()

    st.session_state.scheduler_started = True
    st.session_state.scheduler = scheduler   # Keep reference so it isn't GC'd


st.set_page_config(
    page_title="Market Intelligence Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject minimal custom CSS — Streamlit's dark theme does most of the work
st.markdown("""
<style>
  /* Slightly tighten up metric cards */
  [data-testid="stMetric"] {
      background: #1A1D23;
      border: 1px solid #2A2D35;
      border-radius: 8px;
      padding: 12px 16px;
  }
  /* Remove default top padding from main area */
  .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)



if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Controls")
    st.markdown("---")

    # Asset selector for the comparison chart
    st.subheader("Comparison Chart")
    selected_assets = st.multiselect(
        "Select assets to compare",
        options=ALL_ASSETS,
        default=["BTC", "AAPL"],
    )

    # Prediction horizon
    st.subheader("BTC Prediction")
    future_steps = st.slider("Future steps (×2 min)", min_value=5, max_value=30, value=10)

    st.markdown("---")
    st.caption(f"Display refreshes every {REFRESH_SECS}s")
    st.caption(f"Data collected every {COLLECT_SECS}s")

    # Manual refresh button
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()



df = load_prices()
latest = df.iloc[-1] if not df.empty else {}


st.title("📈 Market Intelligence Dashboard")

# Show how stale the data is
if not df.empty:
    last_ts = df["timestamp"].iloc[-1]
    st.caption(f"Last data point: {last_ts.strftime('%H:%M:%S')}  •  "
               f"{len(df)} rows collected")
else:
    st.info("⏳ Collecting first data point… this takes up to 2 minutes. "
            "The page will refresh automatically.", icon="⏳")


st.subheader("Current Prices")

def make_metric(asset: str, prefix: str = "$"):
    """Render one st.metric card for an asset."""
    if not df.empty and asset in df.columns:
        curr = df[asset].dropna()
        if len(curr) >= 2:
            val  = curr.iloc[-1]
            prev = curr.iloc[-2]
            delta_pct = ((val - prev) / prev) * 100
            delta_str = f"{delta_pct:+.2f}%"
        elif len(curr) == 1:
            val, delta_str = curr.iloc[-1], None
        else:
            val, delta_str = None, None
    else:
        val, delta_str = None, None

    st.metric(
        label=asset,
        value=f"{prefix}{val:,.2f}" if val is not None else "—",
        delta=delta_str,
    )


crypto_cols = st.columns(len(CRYPTO_SYMS))
for col, sym in zip(crypto_cols, CRYPTO_SYMS):
    with col:
        make_metric(sym)

stock_cols = st.columns(len(STOCK_SYMS))
for col, sym in zip(stock_cols, STOCK_SYMS):
    with col:
        make_metric(sym)



st.markdown("---")

# Row 1: Individual crypto charts
st.subheader("Crypto Prices")
chart_colors = {"BTC": "#F7931A", "ETH": "#627EEA", "SOL": "#9945FF", "DOGE": "#C2A633"}

c1, c2, c3, c4 = st.columns(4)
for col, sym in zip([c1, c2, c3, c4], CRYPTO_SYMS):
    with col:
        fig = make_price_chart(df, sym, color=chart_colors[sym])
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{sym}")

# Row 2: Stocks
st.subheader("Stock Prices")
stock_colors = {"AAPL": "#A2AAAD", "TSLA": "#CC0000"}

s1, s2 = st.columns(2)
for col, sym in zip([s1, s2], STOCK_SYMS):
    with col:
        fig = make_price_chart(df, sym, color=stock_colors[sym])
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{sym}")

# Row 3: Comparison + Prediction
st.markdown("---")
col_cmp, col_pred = st.columns(2)

with col_cmp:
    st.subheader("Asset Comparison")
    fig = make_comparison_chart(df, selected_assets or ALL_ASSETS)
    st.plotly_chart(fig, use_container_width=True, key="chart_comparison")

with col_pred:
    st.subheader("BTC Prediction")
    fig = make_btc_prediction_chart(df, future_steps=future_steps)
    st.plotly_chart(fig, use_container_width=True, key="chart_prediction")


elapsed = time.time() - st.session_state.last_refresh
remaining = REFRESH_SECS - elapsed

if remaining <= 0:
    st.session_state.last_refresh = time.time()
    st.rerun()
else:
    # Show a live countdown in the sidebar
    with st.sidebar:
        st.caption(f"⏱ Next refresh in {int(remaining)}s")
    time.sleep(1)        # sleep 1 second, then rerun to update the countdown
    st.session_state.last_refresh = st.session_state.last_refresh  # no-op to avoid lint
    st.rerun()
