import pandas as pd
from engine.feature_engine import FeatureEngine

def test_add_indicators():
df = pd.DataFrame({
	"open": [100]*100,
	"high": [105]*100,
	"low": [95]*100,
	"close": [100]*100,
	"volume": [1000]*100
})
fe = FeatureEngine(df)
enriched = fe.add_indicators()
assert "RSI" in enriched.columns
assert not enriched.isnull().values.any()
