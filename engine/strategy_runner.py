import pandas as pd

class StrategyRunner:
def __init__(self, df: pd.DataFrame):
self.df = df

def run_backtest(self, entry_rule: str, exit_rule: str, sl: float, tp: float) -> dict:
trades = []
position = None
entry_price = 0

for i in range(1, len(self.df)):
	row = self.df.iloc[i]
	prev_row = self.df.iloc[i-1]
	
	# Entry
	if not position and eval(entry_rule, {}, row.to_dict()):
		position = "long"
		entry_price = row["close"]
		entry_index = i
		continue
		
		# Exit
		if position:
			change = (row["close"] - entry_price) / entry_price
			if change >= tp or change <= -sl or eval(exit_rule, {}, row.to_dict()):
				trades.append(change)
				position = None
				
				return {
					"trades": len(trades),
					"average_return": sum(trades) / len(trades) if trades else 0,
					"cumulative_return": sum(trades)
				}
