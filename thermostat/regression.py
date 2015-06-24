import numpy as np
from scipy.stats import linregress

def runtime_regression(hourly_runtime,daily_demand):
    daily_runtime = np.array([runtimes.sum() for day, runtimes in hourly_runtime.groupby(hourly_runtime.index.date)])
    slope, intercept, r_value, p_value, std_err = linregress(daily_demand.values,daily_runtime)
    return slope, intercept, r_value, p_value, std_err
