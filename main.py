from utils.data_loader import OHLCVLoader
from engine.feature_engine import FeatureEngine
from engine.strategy_runner import StrategyRunner
from engine.models import AlphaModel

if __name__ == "__main__":
    # Load and prepare data
    loader = OHLCVLoader("data/eth_usdc_ohlcv.csv")
    df = loader.load()

    # Add indicators
    fe = FeatureEngine(df)
    enriched_df = fe.add_indicators()

    # Train model
    model = AlphaModel()
    enriched_df["target"] = enriched_df["close"].pct_change().shift(-1).apply(lambda x: 1 if x > 0.01 else 0)
    enriched_df = enriched_df.dropna()
    X = enriched_df[["EMA_10", "EMA_50", "RSI", "MACD", "OBV"]]
    y = enriched_df["target"]
    model.train(X, y)
    predictions = model.predict(X)
    print("Sample Predictions:", predictions[:5])

    # Run a sample backtest using basic rules
    runner = StrategyRunner(enriched_df)
    stats = runner.run_backtest(entry_rule="RSI < 30", exit_rule="RSI > 70", sl=0.05, tp=0.10)
    print(stats)
