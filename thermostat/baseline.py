import pandas as pd
import numpy as np

def get_cooling_season_baseline_setpoints(thermostat,cooling_season,method='default'):
    """
    Parameters
    ----------
    thermostat : thermostat.Thermostat
        Thermostat instance for which to gather baseline
    cooling_season : array_like
        Should be an array of booleans with the same length as the temperature
        setpoint data stored in the given thermostat object. True indicates
        presence in the cooling season.
    method : {"default"}, default: "default"
        Method to use in calculation of the baseline.
        - "default": 10th percentile of cooling season setpoints.

    Returns
    -------
    baseline : float
        The baseline cooling setpoint as determined by the given method.
    """
    if method != 'default':
        raise NotImplementedError
    season_setpoints = thermostat.temperature_setpoint[cooling_season]
    setpoint = season_setpoints.quantile(.1)
    return pd.Series(np.tile(setpoint,cooling_season.shape),index=cooling_season.index)

def get_heating_season_baseline_setpoints(thermostat,heating_season,method='default'):
    """
    Parameters
    ----------
    thermostat : thermostat.Thermostat
        Thermostat instance for which to gather baseline
    heating_season : array_like
        Should be an array of booleans with the same length as the temperature
        setpoint data stored in the given thermostat object. True indicates
        presence in the cooling season.
    method : {"default"}, default: "default"
        Method to use in calculation of the baseline.
        - "default": 90th percentile of heating season setpoints.

    Returns
    -------
    baseline : float
        The baseline heating setpoint as determined by the given method.
    """
    if method != 'default':
        raise NotImplementedError
    season_setpoints = thermostat.temperature_setpoint[heating_season]
    setpoint = season_setpoints.quantile(.9)
    return pd.Series(np.tile(setpoint,heating_season.shape),index=heating_season.index)
