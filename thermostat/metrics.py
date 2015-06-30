from thermostat.baseline import get_cooling_season_baseline_setpoints
from thermostat.baseline import get_heating_season_baseline_setpoints
from thermostat.baseline import get_cooling_season_baseline_cooling_demand
from thermostat.baseline import get_heating_season_baseline_heating_demand
from thermostat.demand import get_cooling_demand
from thermostat.demand import get_heating_demand
from thermostat.regression import runtime_regression
from thermostat.savings import get_daily_avoided_runtime
from thermostat.savings import get_total_baseline_cooling_runtime
from thermostat.savings import get_total_baseline_heating_runtime
from thermostat.savings import get_seasonal_percent_savings

def calculate_epa_draft_rccs_field_savings_metrics(thermostat):
    """ Calculates metrics for connected thermostat savings as defined by
    the draft specification defined by the EPA and stakeholders during early
    2015.

    Parameters
    ----------
    thermostat : thermostat.Thermostat
        Thermostat instance for which to calculate metrics

    Returns
    -------
    seasonal_metrics : dict
        Dictionary of heating and cooling seasons. Season names are keys to
        dictionaries of output metrics.
    """
    seasonal_metrics = {}

    for cooling_season, season_name in thermostat.get_cooling_seasons():
        outputs = {}
        outputs["ct_identifier"] = thermostat.thermostat_id
        outputs["zipcode"] = thermostat.zipcode
        outputs["equipment_type"] = thermostat.equipment_type

        baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat,cooling_season)
        outputs["baseline_comfort_temperature"] = baseline_setpoints.iloc[0]

        # calculate demand metrics
        demand_deltaT = get_cooling_demand(thermostat, cooling_season, method="deltaT")
        demand_dailyavgCDD, deltaT_base_est_dailyavgCDD, alpha_est_dailyavgCDD, mean_sq_err_dailyavgCDD = \
                get_cooling_demand(thermostat, cooling_season, method="dailyavgCDD")
        demand_hourlysumCDD, deltaT_base_est_hourlysumCDD, alpha_est_hourlysumCDD, mean_sq_err_hourlysumCDD = \
                get_cooling_demand(thermostat, cooling_season, method="hourlysumCDD")

        # take first column
        hourly_runtime = thermostat.get_cooling_columns()[0][cooling_season]

        # run regressions
        slope_deltaT, intercept_deltaT, mean_sq_err_deltaT = runtime_regression(hourly_runtime, demand_deltaT)
        slope_dailyavgCDD, intercept_dailyavgCDD, mean_sq_err_dailyavgCDD = runtime_regression(hourly_runtime, demand_dailyavgCDD)
        slope_hourlysumCDD, intercept_hourlysumCDD, mean_sq_err_hourlysumCDD = runtime_regression(hourly_runtime, demand_hourlysumCDD)

        outputs["slope_deltaT"] = slope_deltaT
        outputs["slope_dailyavgCDD"] = slope_dailyavgCDD
        outputs["slope_hourlysumCDD"] = slope_hourlysumCDD

        outputs["intercept_deltaT"] = intercept_deltaT
        outputs["intercept_dailyavgCDD"] = intercept_dailyavgCDD
        outputs["intercept_hourlysumCDD"] = intercept_hourlysumCDD

        outputs["mean_squared_error_deltaT"] = mean_sq_err_deltaT
        outputs["mean_squared_error_dailyavgCDD"] = mean_sq_err_dailyavgCDD
        outputs["mean_squared_error_hourlysumCDD"] = mean_sq_err_hourlysumCDD

        actual_seasonal_runtime = thermostat.get_cooling_season_total_runtime(cooling_season)[0]
        n_days = cooling_season.sum() / 24
        actual_daily_runtime = actual_seasonal_runtime / n_days

        outputs["actual_daily_runtime"] = actual_daily_runtime
        outputs["actual_seasonal_runtime"] = actual_seasonal_runtime

        demand_baseline_deltaT = get_cooling_season_baseline_cooling_demand(
                thermostat,cooling_season,baseline_setpoints,method="deltaT")
        demand_baseline_dailyavgCDD = get_cooling_season_baseline_cooling_demand(
                thermostat,cooling_season,baseline_setpoints,deltaT_base_est_dailyavgCDD,method="dailyavgCDD")
        demand_baseline_hourlysumCDD = get_cooling_season_baseline_cooling_demand(
                thermostat,cooling_season,baseline_setpoints,deltaT_base_est_hourlysumCDD,method="hourlysumCDD")

        daily_avoided_runtime_deltaT = get_daily_avoided_runtime(-slope_deltaT,-demand_deltaT,demand_baseline_deltaT)
        daily_avoided_runtime_dailyavgCDD = get_daily_avoided_runtime(slope_dailyavgCDD,demand_dailyavgCDD,demand_baseline_dailyavgCDD)
        daily_avoided_runtime_hourlysumCDD = get_daily_avoided_runtime(slope_hourlysumCDD,demand_hourlysumCDD,demand_baseline_hourlysumCDD)

        baseline_seasonal_runtime_deltaT = \
                get_total_baseline_cooling_runtime(thermostat,cooling_season,daily_avoided_runtime_deltaT)
        baseline_seasonal_runtime_dailyavgCDD = \
                get_total_baseline_cooling_runtime(thermostat,cooling_season,daily_avoided_runtime_dailyavgCDD)
        baseline_seasonal_runtime_hourlysumCDD = \
                get_total_baseline_cooling_runtime(thermostat,cooling_season,daily_avoided_runtime_hourlysumCDD)

        outputs["baseline_seasonal_runtime_deltaT"] = baseline_seasonal_runtime_deltaT
        outputs["baseline_seasonal_runtime_dailyavgCDD"] = baseline_seasonal_runtime_dailyavgCDD
        outputs["baseline_seasonal_runtime_hourlysumCDD"] = baseline_seasonal_runtime_hourlysumCDD

        baseline_daily_runtime_deltaT = baseline_seasonal_runtime_deltaT / n_days
        baseline_daily_runtime_dailyavgCDD = baseline_seasonal_runtime_dailyavgCDD / n_days
        baseline_daily_runtime_hourlysumCDD = baseline_seasonal_runtime_hourlysumCDD / n_days

        outputs["baseline_daily_runtime_deltaT"] = baseline_daily_runtime_deltaT
        outputs["baseline_daily_runtime_dailyavgCDD"] = baseline_daily_runtime_dailyavgCDD
        outputs["baseline_daily_runtime_hourlysumCDD"] = baseline_daily_runtime_hourlysumCDD

        seasonal_savings_deltaT = get_seasonal_percent_savings(baseline_seasonal_runtime_deltaT,daily_avoided_runtime_deltaT)
        seasonal_savings_dailyavgCDD = get_seasonal_percent_savings(baseline_seasonal_runtime_dailyavgCDD,daily_avoided_runtime_dailyavgCDD)
        seasonal_savings_hourlysumCDD = get_seasonal_percent_savings(baseline_seasonal_runtime_hourlysumCDD,daily_avoided_runtime_hourlysumCDD)

        outputs["seasonal_savings_deltaT"] = seasonal_savings_deltaT
        outputs["seasonal_savings_dailyavgCDD"] = seasonal_savings_dailyavgCDD
        outputs["seasonal_savings_hourlysumCDD"] = seasonal_savings_hourlysumCDD

        seasonal_avoided_runtime_deltaT = daily_avoided_runtime_deltaT.mean()
        seasonal_avoided_runtime_dailyavgCDD = daily_avoided_runtime_dailyavgCDD.mean()
        seasonal_avoided_runtime_hourlysumCDD = daily_avoided_runtime_hourlysumCDD.mean()

        outputs["seasonal_avoided_runtime_deltaT"] = seasonal_avoided_runtime_deltaT
        outputs["seasonal_avoided_runtime_dailyavgCDD"] = seasonal_avoided_runtime_dailyavgCDD
        outputs["seasonal_avoided_runtime_hourlysumCDD"] = seasonal_avoided_runtime_hourlysumCDD

        seasonal_metrics[season_name] = outputs

    for heating_season, season_name in thermostat.get_heating_seasons():
        outputs = {}
        outputs["ct_identifier"] = thermostat.thermostat_id
        outputs["zipcode"] = thermostat.zipcode
        outputs["equipment_type"] = thermostat.equipment_type

        baseline_setpoints = get_heating_season_baseline_setpoints(thermostat,heating_season)
        outputs["baseline_comfort_temperature"] = baseline_setpoints.iloc[0]

        seasonal_metrics[season_name] = outputs

    return seasonal_metrics
