import pandas as pd

def seasonal_metrics_to_csv(seasonal_metrics, filepath):
    pd.DataFrame(seasonal_metrics).to_csv(filepath, index=False)
