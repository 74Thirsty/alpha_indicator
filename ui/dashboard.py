import streamlit as st
import pandas as pd
from engine.feature_engine import FeatureEngine
from utils.data_loader import OHLCVLoader

st.set_page_config(layout="wide")
st.title("📈 AlphaEdge Dashboard")

# Load CSV
csv_file = st.file_uploader("Upload OHLCV CSV", type=["csv"])
if csv_file:
    df = pd.read_csv(csv_file)
    loader = OHLCVLoader(csv_file)
    raw = loader.load()
    fe = FeatureEngine(raw)
    enriched = fe.add_indicators()

    st.subheader("Enriched Indicators")
    st.dataframe(enriched.tail())

    st.line_chart(enriched[["close", "EMA_10", "EMA_50"]].dropna())
    st.line_chart(enriched[["RSI"]].dropna())
    st.line_chart(enriched[["MACD"]].dropna())

