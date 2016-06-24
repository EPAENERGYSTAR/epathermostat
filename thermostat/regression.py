import numpy as np
import pandas as pd
from scipy.optimize import leastsq

def runtime_regression(daily_runtime, daily_demand, method):
    """
    Least squares regession of runtime against a measure of demand.

    Parameters
    ----------
    hourly_runtime : pd.Series with pd.DatetimeIndex
        Runtimes for a particular heating or cooling season.
    daily_demand : pd.Series with pd.DatetimeIndex
        A daily demand measure for each day in the heating or cooling season.

    Returns
    -------
    slope : float
        The slope parameter found by the regression to minimize sq error
    intercept : float
        The intercept parameter found by the regression to minimize sq error
    mean_sq_err : float
        The mean squared error of the regession.
    root_mean_sq_err : float
        The root mean squared error of the regession.
    """

    # drop NA
    df = pd.DataFrame({"x": daily_demand, "y": daily_runtime}).dropna()
    x, y = df.x, df.y

    if method == "cooling":
        def model(params):
            alpha, tau = params
            return y - (alpha * (x + tau))

    else:
        def model(params):
            alpha, tau = params
            return y - (alpha * (x - tau))

    x0 = (1, 0)

    try:
        results = leastsq(model, x0)
    except TypeError:
        # too few data points causes the following TypeError
        # TypeError: Improper input: N=2 must not exceed M=1
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

    params = results[0]
    alpha, tau = params
    mse = np.nanmean(model(params)**2)
    rmse = mse ** 0.5
    cvrmse = rmse / np.nanmean(y)
    mape = np.nanmean(np.absolute(model(params) / y))
    mae = np.nanmean(np.absolute(model(params)))

    return alpha, tau, mse, rmse, cvrmse, mape, mae
