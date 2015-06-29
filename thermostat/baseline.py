import pandas as pd
import numpy as np

def get_cooling_season_baseline_setpoints(thermostat,cooling_season,method='tenth_percentile'):
    """ Calculate the cooling season baseline setpoint (comfort temperature).

    Parameters
    ----------
    thermostat : thermostat.Thermostat
        Thermostat instance for which to gather baseline
    cooling_season : array_like
        Should be an array of booleans with the same length as the temperature
        setpoint data stored in the given thermostat object. True indicates
        presence in the cooling season.
    method : {"tenth_percentile"}, default: "tenth_percentile"
        Method to use in calculation of the baseline.

        - "tenth_percentile": 10th percentile of cooling season setpoints.

    Returns
    -------
    baseline : pandas.Series
        The baseline cooling setpoint for the cooling season as determined by
        the given method.
    """
    if method != 'tenth_percentile':
        raise NotImplementedError
    season_setpoints = thermostat.temperature_setpoint[cooling_season]
    setpoint = season_setpoints.quantile(.1)
    return pd.Series(np.tile(setpoint,cooling_season.shape),index=cooling_season.index)

def get_heating_season_baseline_setpoints(thermostat,heating_season,method='ninetieth_percentile'):
    """ Calculate the heating season baseline setpoint (comfort temperature).

    Parameters
    ----------
    thermostat : thermostat.Thermostat
        Thermostat instance for which to gather baseline
    heating_season : array_like
        Should be an array of booleans with the same length as the temperature
        setpoint data stored in the given thermostat object. True indicates
        presence in the cooling season.
    method : {"ninetieth_percentile"}, default: "ninetieth_percentile"
        Method to use in calculation of the baseline.

        - "ninetieth_percentile": 90th percentile of heating season setpoints.

    Returns
    -------
    baseline : pandas.Series
        The baseline heating setpoint for the heating season as determined by
        the given method.
    """
    if method != 'ninetieth_percentile':
        raise NotImplementedError
    season_setpoints = thermostat.temperature_setpoint[heating_season]
    setpoint = season_setpoints.quantile(.9)
    return pd.Series(np.tile(setpoint,heating_season.shape),index=heating_season.index)

def get_cooling_season_baseline_cooling_demand(thermostat,cooling_season,baseline_setpoint,deltaT_base=None,method="deltaT"):
    """ Calculate baseline cooling degree days for a particular cooling season
    and baseline setpoint.

    Parameters
    ----------
    thermostat : thermostat.Thermostat
        Thermostat instance for which to compute cooling season baseline
    cooling_season : array_like
        Should be an array of booleans with the same length as the data stored
        in the given thermostat object. True indicates presence in the cooling
        season.
    baseline_setpoint : pandas.Series
        A series containing the baseline setpoint at every hour in the cooling
        season.
    deltaT_base : float, default: None
        Used in calculations for "dailyavgHDD" and "hourlysumHDD".
    method : {"deltaT", "dailyavgCDD", "hourlysumCDD"}; default: "deltaT"
        Method to use in calculation of the baseline cdd.

        - "deltaT": :math:`\Delta T_{\\text{base cool}} = \\text{daily avg }
          T_{\\text{outdoor}} - T_{\\text{base cool}}`
        - "dailyavgCDD": :math:`\\text{CDD}_{\\text{base}} = \Delta T_{\\text{base
          cool}} - \Delta T_{\\text{b cool}}` where :math:`\Delta T_{\\text{base
          cool}} = \\text{daily avg } T_{\\text{outdoor}} - T_{\\text{base cool}}`
        - "hourlysumCDD": :math:`\\text{CDD}_{\\text{base}} = \\frac{\sum_{i=1}^
          {24} \\text{CDH}_{\\text{base } i}}{24}` where :math:`\\text{CDH}_{
          \\text{base } i} = \Delta T_{\\text{base cool}} - \Delta T_{\\text{b
          cool}}` and :math:`\Delta T_{\\text{base cool}} = T_{\\text{outdoor}}
          - T_{\\text{base cool}}`

    Returns
    -------
    baseline_cooling_demand : pandas.Series
        A series containing baseline daily heating demand for the cooling season.
    """
    temp_baseline = baseline_setpoint.iloc[0] # assumes all are the same
    season_temp_out = thermostat.temperature_out[cooling_season]

    index = pd.to_datetime([day for day,_ in season_temp_out.groupby(season_temp_out.index.date)])
    daily_temp_out = np.array([temps.mean() for day, temps in season_temp_out.groupby(season_temp_out.index.date)])

    if method == "deltaT":
        demand = daily_temp_out - temp_baseline
    elif method == "dailyavgCDD":
        demand = np.maximum(daily_temp_out - temp_baseline - deltaT_base,0)
    elif method == "hourlysumCDD":
        hourly_cdd = (season_temp_out - temp_baseline - deltaT_base).apply(lambda x: np.maximum(x,0))
        demand = np.array([cdd.sum() / 24 for day, cdd in hourly_cdd.groupby(season_temp_out.index.date)])
    else:
        raise NotImplementedError
    return pd.Series(demand, index=index)

def get_heating_season_baseline_heating_demand(thermostat,heating_season,baseline_setpoint,deltaT_base=None,method="deltaT"):
    """ Calculate baseline heating degree days for a particular heating season
    and baseline setpoint.

    Parameters
    ----------
    thermostat : thermostat.Thermostat
        Thermostat instance for which to compute heating season baseline
    heating_season : array_like
        Should be an array of booleans with the same length as the data stored
        in the given thermostat object. True indicates presence in the heating
        season.
    baseline_setpoint : pandas.Series
        A series containing the baseline setpoint at every hour in the heating
        season.
    deltaT_base : float, default: None
        Used in calculations for "dailyavgHDD" and "hourlysumHDD".
    method : {"deltaT", "dailyavgHDD", "hourlysumHDD"}; default: "deltaT"
        Method to use in calculation of the baseline cdd.

        - "deltaT": :math:`\Delta T_{\\text{base heat}} = T_{\\text{base heat}}
          - \\text{daily avg } T_{\\text{outdoor}}`
        - "dailyavgHDD": :math:`\\text{HDD}_{\\text{base}} = \Delta T_{\\text{base
          heat}} - \Delta T_{\\text{b heat}}` where :math:`\Delta T_{\\text{base
          heat}} = T_{\\text{base heat}} - \\text{daily avg } T_{\\text{outdoor}}`
        - "hourlysumHDD": :math:`\\text{HDD}_{\\text{base}} = \\frac{\sum_{i=1}^
          {24} \\text{HDH}_{\\text{base } i}}{24}` where :math:`\\text{HDH}_{
          \\text{base } i} = \Delta T_{\\text{base heat}} - \Delta T_{\\text{b
          heat}}` and :math:`\Delta T_{\\text{base heat}} = T_{\\text{base heat}}
          - T_{\\text{outdoor}}`

    Returns
    -------
    baseline_heating_demand : pandas.Series
        A series containing baseline daily heating demand for the heating season.
    """
    temp_baseline = baseline_setpoint.iloc[0] # assumes all are the same
    season_temp_out = thermostat.temperature_out[heating_season]

    index = pd.to_datetime([day for day,_ in season_temp_out.groupby(season_temp_out.index.date)])
    daily_temp_out = np.array([temps.mean() for day, temps in season_temp_out.groupby(season_temp_out.index.date)])

    if method == "deltaT":
        demand = temp_baseline - daily_temp_out
    elif method == "dailyavgHDD":
        demand = np.maximum(temp_baseline - daily_temp_out - deltaT_base,0)
    elif method == "hourlysumHDD":
        hourly_hdd = (temp_baseline - season_temp_out - deltaT_base).apply(lambda x: np.maximum(x,0))
        demand = np.array([hdd.sum() / 24 for day, hdd in hourly_hdd.groupby(season_temp_out.index.date)])
    else:
        raise NotImplementedError
    return pd.Series(demand, index=index)
