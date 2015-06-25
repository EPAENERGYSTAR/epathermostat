import numpy as np
from numpy.linalg import lstsq

def runtime_regression(hourly_runtime,daily_demand):
    """
    Calculates a runtime regression against a measure of demand.

    Parameters
    ----------
    hourly_runtime : pd.Series with pd.DatetimeIndex
        Runtimes for a particular heating or cooling season.
    daily_demand : pd.Series with pd.DatetimeIndex
        A daily demand measure for each day in the heating or cooling season.
    """
    daily_runtime = np.array([runtimes.sum() for day, runtimes in hourly_runtime.groupby(hourly_runtime.index.date)])
    x_1 = daily_demand.values[:,np.newaxis]
    x_0 = np.tile(1,x_1.shape)
    x = np.concatenate((x_1,x_0),axis=1)
    y = daily_runtime
    results = lstsq(x,y) # model: y = a*x
    slope,intercept = results[0]
    mean_sq_err = results[1][0] / y.shape[0] # convert from sum sq err
    return slope, intercept, mean_sq_err

