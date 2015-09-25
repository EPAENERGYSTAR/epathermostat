def get_daily_avoided_runtime(alpha, demand, demand_baseline):
    """ Calculate avoided runtime from an estimate of alpha, demand and demand
    baseline for heating or cooling seasons. Expects the sign of demand to be
    such that it correlates positively with runtime.

    Parameters
    ----------
    alpha : float
        Estimate of slope of runtime response to demand.
    demand : pandas.Series
        Timeseries of daily demand for a particular season.
    demand_baseline : pandas.Series
        Timeseries of baseline daily demand for a particular season.

    Returns
    -------
    daily_avoided_runtime : pandas.Series
        Timeseries of daily avoided runtime.
    """
    return alpha * (demand_baseline - demand)

def get_seasonal_percent_savings(total_baseline_runtime, daily_avoided_runtime):
    """ Estimate baseline heating runtime given a daily avoided runtimes.

    Parameters
    ----------
    total_baseline_runtime : pandas.Series
        Total baseline season runtime for a particular season
    daily_avoided_runtime : pandas.Series
        Timeseries of daily avoided runtime for a particular season.

    Returns
    -------
    seasonal_percent_savings : pandas.Series
        Seasonal percent savings as given by :math:`\\text{seasonal percent
        savings} = \\frac{\\text{seasonal avoided runtime}}{\\text{baseline
        seasonal runtime}}`. Returned as a decimal.
    """
    total_avoided_runtime = daily_avoided_runtime.sum()

    seasonal_percent_savings = total_avoided_runtime / total_baseline_runtime
    return seasonal_percent_savings
