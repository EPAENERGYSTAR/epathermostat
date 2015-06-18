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
    method : {"deltaT", "hourlysumCDD", "dailyavgCDD"}, default: "deltaT"
        The method to use during calculation of demand.

        - "deltaT": :math:`\Delta T = temp_{in} - temp_{out}`

    Returns
    -------
    demand : pd.Series
        Demand at each hour in the heating season as calculated using one of
        the supported methods.
    """
    if method == "deltaT":
        season_temp_in = thermostat.temperature_in[cooling_season]
        season_temp_out = thermostat.temperature_out[cooling_season]
        demand = season_temp_in - season_temp_out
        return demand
    elif method == "hourlysumCDD":
        raise NotImplementedError
    elif method == "dailyavgCDD":
        raise NotImplementedError
    else:
        raise NotImplementedError

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

    Returns
    -------
    demand : pd.Series
        Demand at each hour in the heating season as calculated using one of
        the supported methods.
    """
    if method == "deltaT":
        season_temp_in = thermostat.temperature_in[heating_season]
        season_temp_out = thermostat.temperature_out[heating_season]
        demand = season_temp_in - season_temp_out
        return demand
    elif method == "hourlysumHDD":
        raise NotImplementedError
    elif method == "dailyavgHDD":
        raise NotImplementedError
    else:
        raise NotImplementedError
