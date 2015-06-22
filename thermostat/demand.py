import numpy as np
from scipy.optimize import leastsq

def get_cooling_demand(thermostat,cooling_season,method="deltaT",column_name=None):
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
    method : {"deltaT", "hourlysumCDD", "dailyavgCDD"}, default: "deltaT"
        The method to use during calculation of demand.

        - "deltaT": :math:`\Delta T = temp_{in} - temp_{out}`
    column_name : str
        The name of the column for which to calculate demand estimates which use
        runtime to optimize CDD base temperature ("hourlysumCDD" and
        "dailyavgCDD").

    Returns
    -------
    demand : pd.Series
        Demand at each hour in the heating season as calculated using one of
        the supported methods.
    """
    season_temp_in = thermostat.temperature_in[cooling_season]
    season_temp_out = thermostat.temperature_out[cooling_season]
    season_deltaT = season_temp_in - season_temp_out

    if method == "deltaT":
        return season_deltaT
    elif method == "dailyavgCDD":
        daily_avg_deltaT = np.array([-temps.mean() for day, temps in season_deltaT.groupby(season_deltaT.index.date)])
        def calc_cdd(deltaT_base):
            return np.maximum(daily_avg_deltaT - deltaT_base,0)
    elif method == "hourlysumCDD":
        def calc_cdd(deltaT_base):
            hourly_cdd = (-season_deltaT - deltaT_base).apply(lambda x: np.maximum(x,0))
            return np.array([cdd.sum() / 24 for day, cdd in hourly_cdd.groupby(season_deltaT.index.date)])
    else:
        raise NotImplementedError

    cooling_column = thermostat.__dict__.get(column_name)
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

    return cdd, deltaT_base_estimate, alpha_estimate, mean_squared_error

def get_heating_demand(thermostat,heating_season,method="deltaT",column_name=None):
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
    column_name : str
        The name of the column for which to calculate demand estimates which use
        runtime to optimize HDD base temperature ("hourlysumHDD" and
        "dailyavgHDD").

    Returns
    -------
    demand : pd.Series
        Demand at each hour in the heating season as calculated using one of
        the supported methods.
    """
    season_temp_in = thermostat.temperature_in[heating_season]
    season_temp_out = thermostat.temperature_out[heating_season]
    season_deltaT = season_temp_in - season_temp_out

    if method == "deltaT":
        return season_deltaT
    elif method == "dailyavgHDD":
        daily_avg_deltaT = np.array([temps.mean() for day, temps in season_deltaT.groupby(season_deltaT.index.date)])
        def calc_hdd(deltaT_base):
            return np.maximum(daily_avg_deltaT - deltaT_base,0)
    elif method == "hourlysumHDD":
        def calc_hdd(deltaT_base):
            hourly_hdd = (season_deltaT - deltaT_base).apply(lambda x: np.maximum(x,0))
            return np.array([hdd.sum() / 24 for day, hdd in hourly_hdd.groupby(season_deltaT.index.date)])
    else:
        raise NotImplementedError

    heating_column = thermostat.__dict__.get(column_name)
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

    return hdd, deltaT_base_estimate, alpha_estimate, mean_squared_error
