import pandas as pd

def seasonal_metrics_to_csv(seasonal_metrics, filepath):
    rows = []
    for outputs in seasonal_metrics:
        rows.append(outputs)

    pd.DataFrame(rows).to_csv(filepath, index=False)
