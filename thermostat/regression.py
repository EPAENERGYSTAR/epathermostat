import numpy as np
from numpy.linalg import lstsq

def runtime_regression(daily_runtime, daily_demand):
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
    """
    x = daily_demand.values[:,np.newaxis]
    # x_0 = np.tile(1, x_1.shape)
    # x = np.concatenate((x_1,x_0), axis=1)
    y = daily_runtime
    results = lstsq(x, y) # model: y = a*x
    slope = results[0][0]
    mean_sq_err = results[1][0] / y.shape[0] # convert from sum sq err
    return slope, mean_sq_err

