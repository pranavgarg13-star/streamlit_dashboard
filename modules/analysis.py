

import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "prices.csv")




def ensure_data_dir():
    """Create the data/ folder if it doesn't exist yet."""
    os.makedirs(DATA_DIR, exist_ok=True)


def save_prices(prices: dict):
    
    ensure_data_dir()

    row = {"timestamp": datetime.now().isoformat(), **prices}
    df_new = pd.DataFrame([row])

    if os.path.exists(CSV_PATH):
        df_new.to_csv(CSV_PATH, mode="a", header=False, index=False)
    else:
        df_new.to_csv(CSV_PATH, index=False)


def load_prices() -> pd.DataFrame:
 
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=["timestamp"])

    df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])

    # Drop duplicate timestamps (can happen if the scheduler fires twice quickly)
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    return df


# ── Chart builders ─────────────────────────────────────────────────────────────

def _base_fig(title: str) -> go.Figure:
    """Shared dark-theme layout used by all charts."""
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#E0E0E0")),
        paper_bgcolor="#0E1117",   # matches Streamlit's dark background
        plot_bgcolor="#1A1D23",
        font=dict(color="#C0C0C0"),
        xaxis=dict(gridcolor="#2A2D35", showgrid=True),
        yaxis=dict(gridcolor="#2A2D35", showgrid=True),
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
    )
    return fig


def make_price_chart(df: pd.DataFrame, asset: str, color: str = "#00C4FF") -> go.Figure:
    """
    Line chart for a single asset over time.

    df:    full history DataFrame (from load_prices)
    asset: column name, e.g. "BTC" or "AAPL"
    color: hex color for the line
    """
    fig = _base_fig(f"{asset} Price Over Time")

    if asset not in df.columns or df.empty:
        # Return an empty chart with a message rather than crashing
        fig.add_annotation(
            text="Collecting data — check back in a minute",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#888"),
        )
        return fig

    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df[asset],
        mode="lines",
        name=asset,
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
    ))
    return fig


def make_comparison_chart(df: pd.DataFrame, assets: list[str]) -> go.Figure:
    """
    Normalised multi-asset comparison chart.

    All assets start at 100 so you can compare % movement regardless
    of their very different absolute prices (BTC vs AAPL etc.).
    """
    fig = _base_fig("Asset Comparison (Indexed to 100)")
    colors = ["#00C4FF", "#FF6B6B", "#FFD93D", "#6BCB77", "#C77DFF"]

    for i, asset in enumerate(assets):
        if asset not in df.columns or df[asset].dropna().empty:
            continue
        series = df[asset].dropna()
        # Normalise: divide every value by the first value × 100
        normalised = (series / series.iloc[0]) * 100

        fig.add_trace(go.Scatter(
            x=df.loc[series.index, "timestamp"],
            y=normalised,
            mode="lines",
            name=asset,
            line=dict(color=colors[i % len(colors)], width=2),
        ))

    return fig


def make_btc_prediction_chart(df: pd.DataFrame, future_steps: int = 10) -> go.Figure:
    """
    BTC linear regression prediction chart.

    Uses minute-level index as the X variable (simpler than datetime maths
    and sufficient for short-range extrapolation).
    """
    from sklearn.linear_model import LinearRegression
    import numpy as np

    fig = _base_fig("BTC Price Prediction (Linear Regression)")

    if "BTC" not in df.columns or len(df["BTC"].dropna()) < 5:
        fig.add_annotation(
            text="Need at least 5 data points for prediction",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#888"),
        )
        return fig

    btc = df[["timestamp", "BTC"]].dropna().reset_index(drop=True)
    X = btc.index.values.reshape(-1, 1)
    y = btc["BTC"].values

    model = LinearRegression()
    model.fit(X, y)

    # Future indices beyond the last data point
    future_X = np.arange(len(X), len(X) + future_steps).reshape(-1, 1)
    future_y = model.predict(future_X)

    # Fake future timestamps (each step = 2 minutes, matching scheduler interval)
    last_ts = btc["timestamp"].iloc[-1]
    future_ts = pd.date_range(start=last_ts, periods=future_steps + 1, freq="2min")[1:]

    # Historical line
    fig.add_trace(go.Scatter(
        x=btc["timestamp"], y=y,
        mode="lines", name="Actual",
        line=dict(color="#00C4FF", width=2),
    ))
    # Predicted line
    fig.add_trace(go.Scatter(
        x=future_ts, y=future_y,
        mode="lines+markers", name="Predicted",
        line=dict(color="#FF6B6B", width=2, dash="dash"),
    ))

    return fig
