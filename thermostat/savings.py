def get_daily_avoided_runtime(alpha,demand,demand_baseline):
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

def get_total_baseline_cooling_runtime(thermostat,cooling_season,daily_avoided_runtime):
    """ Estimate baseline cooling runtime given a daily avoided runtimes.

    Parameters
    ----------
    thermostat : thermostat.Thermostat
        The thermostat for which to estimate total baseline cooling runtime.
    cooling_season : pandas.Series
        Timeseries of booleans in hourly resolution representing the cooling
        season for which to estimate total baseline cooling.
    daily_avoided_runtime : pandas.Series
        Timeseries of daily avoided runtime for a particular cooling season.

    Returns
    -------
    total_baseline_cooling_runtime : pandas.Series
        Total baseline cooling runtime for the given season and thermostat.
    """
    total_avoided_runtime = daily_avoided_runtime.sum()

    # take the first column (there should only be exactly one!)
    total_actual_runtime = thermostat.get_cooling_season_total_runtime(cooling_season)[0]

    total_baseline_cooling_runtime = total_actual_runtime - total_avoided_runtime
    return total_baseline_cooling_runtime

def get_total_baseline_heating_runtime(thermostat,heating_season,daily_avoided_runtime):
    """ Estimate baseline heating runtime given a daily avoided runtimes.

    Parameters
    ----------
    thermostat : thermostat.Thermostat
        The thermostat for which to estimate total baseline heating runtime.
    heating_season : pandas.Series
        Timeseries of booleans in hourly resolution representing the heating
        season for which to estimate total baseline heating.
    daily_avoided_runtime : pandas.Series
        Timeseries of daily avoided runtime for a particular heating season.

    Returns
    -------
    total_baseline_heating_runtime : pandas.Series
        Total baseline heating runtime for the given season and thermostat.
    """
    total_avoided_runtime = daily_avoided_runtime.sum()

    # take the first column (there should only be exactly one!)
    total_actual_runtime = thermostat.get_heating_season_total_runtime(heating_season)[0]

    total_baseline_heating_runtime = total_actual_runtime - total_avoided_runtime
    return total_baseline_heating_runtime

def get_seasonal_percent_savings(total_baseline_runtime,daily_avoided_runtime):
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
