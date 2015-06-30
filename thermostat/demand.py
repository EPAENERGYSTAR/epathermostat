import pandas as pd
import numpy as np
from scipy.optimize import leastsq

def get_cooling_demand(thermostat,cooling_season,method="deltaT"):
    """
    Calculates a measure of cooling demand.

    Parameters
    ----------
    thermostat : thermostat.Thermostat
        The thermostat instance for which to calculate heating demand.
    cooling_season : array_like
        Should be an array of booleans with the same length as the temperature
        setpoint data stored in the given thermostat object. True indicates
        presence in the cooling season.
    method : {"deltaT", "dailyavgCDD", "hourlysumCDD"}, default: "deltaT"
        The method to use during calculation of demand.

        - "deltaT": :math:`\Delta T = temp_{in} - temp_{out}`
        - "dailyavgCDD": :math:`\\text{daily CDD} = \Delta T_{\\text{daily avg}}
          - \Delta T_{\\text{base cool}}` where
          :math:`\Delta T_{\\text{daily avg}} =
          \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
        - "hourlysumCDD": :math:`\\text{daily CDD} = \sum_{i=1}^{24} \\text{CDH}_i`
          where :math:`\\text{CDH}_i = \Delta T_i - \Delta T_{\\text{base cool}}`

    Returns
    -------
    demand : pd.Series
        Daily demand in the heating season as calculated using one of
        the supported methods.
    deltaT_base_estimate : float
        Estimate of :math:`\Delta T_{\\text{base cool}}`. Only output for
        "hourlysumCDD" and "dailyavgCDD".
    alpha_estimate : float
        Estimate of linear runtime response to demand. Only output for
        "hourlysumCDD" and "dailyavgCDD".
    mean_squared_error : float
        Mean squared error in runtime estimates. Only output for "hourlysumCDD"
        and "dailyavgCDD".
    """
    season_temp_in = thermostat.temperature_in[cooling_season]
    season_temp_out = thermostat.temperature_out[cooling_season]
    season_deltaT = season_temp_in - season_temp_out

    daily_avg_deltaT = np.array([temps.mean() for day, temps in season_deltaT.groupby(season_deltaT.index.date)])
    index = pd.to_datetime([day for day, _ in season_deltaT.groupby(season_deltaT.index.date)])

    if method == "deltaT":
        return pd.Series(daily_avg_deltaT, index=index)
    elif method == "dailyavgCDD":
        def calc_cdd(deltaT_base):
            return np.maximum(deltaT_base - daily_avg_deltaT,0)
    elif method == "hourlysumCDD":
        def calc_cdd(deltaT_base):
            hourly_cdd = (deltaT_base - season_deltaT).apply(lambda x: np.maximum(x,0))
            return np.array([cdd.sum() / 24 for day, cdd in hourly_cdd.groupby(season_deltaT.index.date)])
    else:
        raise NotImplementedError

    cooling_column = thermostat.get_cooling_columns()[0]
    cooling_runtime = cooling_column[cooling_season]

    # calculate daily runtimes by taking the average hourly then multiplying by 24
    # - this attempts to account for partial days (which may occur at endpoints)
    daily_runtime = np.array([runtimes.mean() * 24 for day, runtimes in cooling_runtime.groupby(cooling_runtime.index.date)])
    total_runtime = cooling_runtime.sum()

    def calc_estimates(deltaT_base):
        cdd = calc_cdd(deltaT_base)
        total_cdd = np.sum(cdd)
        alpha_estimate = total_runtime / total_cdd
        runtime_estimate = cdd * alpha_estimate
        errors = daily_runtime - runtime_estimate
        return cdd, alpha_estimate, errors

    def estimate_errors(deltaT_base_estimate):
        _,_,errors = calc_estimates(deltaT_base_estimate)
        return errors

    deltaT_base_starting_guess = 0
    y, _ = leastsq(estimate_errors, deltaT_base_starting_guess)
    deltaT_base_estimate = y[0]

    cdd, alpha_estimate, errors = calc_estimates(deltaT_base_estimate)
    mean_squared_error = np.mean((errors)**2)

    return pd.Series(cdd, index=index), deltaT_base_estimate, alpha_estimate, mean_squared_error

def get_heating_demand(thermostat,heating_season,method="deltaT"):
    """
    Calculates a measure of heating demand.

    Parameters
    ----------
    thermostat : thermostat.Thermostat
        The thermostat instance for which to calculate heating demand.
    heating_season : array_like
        Should be an array of booleans with the same length as the temperature
        setpoint data stored in the given thermostat object. True indicates
        presence in the heating season.
    method : {"deltaT", "hourlysumHDD", "dailyavgHDD"} default: "deltaT"
        The method to use during calculation of demand.

        - "deltaT": :math:`\Delta T = temp_{in} - temp_{out}`
        - "dailyavgHDD": :math:`\\text{daily HDD} = \Delta T_{\\text{daily avg}}
          - \Delta T_{\\text{base heat}}` where
          :math:`\Delta T_{\\text{daily avg}} =
          \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
        - "hourlysumHDD": :math:`\\text{daily HDD} = \sum_{i=1}^{24} \\text{HDH}_i`
          where :math:`\\text{HDH}_i = \Delta T_i - \Delta T_{\\text{base heat}}`

    Returns
    -------
    demand : pd.Series
        Daily demand in the heating season as calculated using one of
        the supported methods.
    deltaT_base_estimate : float
        Estimate of :math:`\Delta T_{\\text{base heat}}`. Only output for
        "hourlysumHDD" and "dailyavgHDD".
    alpha_estimate : float
        Estimate of linear runtime response to demand. Only output for
        "hourlysumHDD" and "dailyavgHDD".
    mean_squared_error : float
        Mean squared error in runtime estimates. Only output for "hourlysumHDD"
        and "dailyavgHDD".
    """
    season_temp_in = thermostat.temperature_in[heating_season]
    season_temp_out = thermostat.temperature_out[heating_season]
    season_deltaT = season_temp_in - season_temp_out

    daily_avg_deltaT = np.array([temps.mean() for day, temps in season_deltaT.groupby(season_deltaT.index.date)])
    index = pd.to_datetime([day for day, _ in season_deltaT.groupby(season_deltaT.index.date)])

    if method == "deltaT":
        return pd.Series(daily_avg_deltaT, index=index)
    elif method == "dailyavgHDD":
        def calc_hdd(deltaT_base):
            return np.maximum(daily_avg_deltaT - deltaT_base,0)
    elif method == "hourlysumHDD":
        def calc_hdd(deltaT_base):
            hourly_hdd = (season_deltaT - deltaT_base).apply(lambda x: np.maximum(x,0))
            return np.array([hdd.sum() / 24 for day, hdd in hourly_hdd.groupby(season_deltaT.index.date)])
    else:
        raise NotImplementedError

    heating_column = thermostat.get_heating_columns()[0]
    heating_runtime = heating_column[heating_season]

    # calculate daily runtimes by taking the average hourly then multiplying by 24
    # - this attempts to account for partial days (which may occur at endpoints)
    daily_runtime = np.array([runtimes.mean() * 24 for day, runtimes in heating_runtime.groupby(heating_runtime.index.date)])
    total_runtime = heating_runtime.sum()

    def calc_estimates(deltaT_base):
        hdd = calc_hdd(deltaT_base)
        total_hdd = np.sum(hdd)
        alpha_estimate = total_runtime / total_hdd
        runtime_estimate = hdd * alpha_estimate
        errors = daily_runtime - runtime_estimate
        return hdd, alpha_estimate, errors

    def estimate_errors(deltaT_base_estimate):
        _, _, errors = calc_estimates(deltaT_base_estimate)
        return errors

    deltaT_base_starting_guess = 0
    y, _ = leastsq(estimate_errors, deltaT_base_starting_guess)
    deltaT_base_estimate = y[0]

    hdd, alpha_estimate, errors = calc_estimates(deltaT_base_estimate)
    mean_squared_error = np.mean((errors)**2)

    return pd.Series(hdd, index=index), deltaT_base_estimate, alpha_estimate, mean_squared_error
