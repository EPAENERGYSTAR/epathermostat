def get_cooling_season_baseline(thermostat,cooling_season,method='default'):
    """
    Parameters
    ----------
    thermostat : thermostat.Thermostat
        Thermostat instance for which to gather baseline
    cooling_season : array_like
        Should be an array of booleans with the same length as the temperature
        setpoint data stored in the given thermostat object. True indicates
        presence in the cooling season.
    """
    if method != 'default':
        raise NotImplementedError
    season_setpoints = thermostat.temperature_setpoint[cooling_season]
    return season_setpoints.quantile(.1)

def get_heating_season_baseline(thermostat,heating_season,method='default'):
    """
    Parameters
    ----------
    thermostat : thermostat.Thermostat
        Thermostat instance for which to gather baseline
    heating_season : array_like
        Should be an array of booleans with the same length as the temperature
        setpoint data stored in the given thermostat object. True indicates
        presence in the cooling season.
    """
    if method != 'default':
        raise NotImplementedError
    season_setpoints = thermostat.temperature_setpoint[heating_season]
    return season_setpoints.quantile(.9)
