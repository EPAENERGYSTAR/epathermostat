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

import pandas as pd

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

        seasonal_avoided_runtime_deltaT = daily_avoided_runtime_deltaT.sum()
        seasonal_avoided_runtime_dailyavgCDD = daily_avoided_runtime_dailyavgCDD.sum()
        seasonal_avoided_runtime_hourlysumCDD = daily_avoided_runtime_hourlysumCDD.sum()

        outputs["seasonal_avoided_runtime_deltaT"] = seasonal_avoided_runtime_deltaT
        outputs["seasonal_avoided_runtime_dailyavgCDD"] = seasonal_avoided_runtime_dailyavgCDD
        outputs["seasonal_avoided_runtime_hourlysumCDD"] = seasonal_avoided_runtime_hourlysumCDD

        n_days_both, n_days_incomplete = thermostat.get_season_ignored_days(season_name)

        outputs["n_days_both_heating_and_cooling"] = n_days_both
        outputs["n_days_incomplete"] = n_days_incomplete

        seasonal_metrics[season_name] = outputs

    for heating_season, season_name in thermostat.get_heating_seasons():
        outputs = {}
        outputs["ct_identifier"] = thermostat.thermostat_id
        outputs["zipcode"] = thermostat.zipcode
        outputs["equipment_type"] = thermostat.equipment_type

        baseline_setpoints = get_heating_season_baseline_setpoints(thermostat,heating_season)
        outputs["baseline_comfort_temperature"] = baseline_setpoints.iloc[0]

        # calculate demand metrics
        demand_deltaT = get_heating_demand(thermostat, heating_season, method="deltaT")
        demand_dailyavgHDD, deltaT_base_est_dailyavgHDD, alpha_est_dailyavgHDD, mean_sq_err_dailyavgHDD = \
                get_heating_demand(thermostat, heating_season, method="dailyavgHDD")
        demand_hourlysumHDD, deltaT_base_est_hourlysumHDD, alpha_est_hourlysumHDD, mean_sq_err_hourlysumHDD = \
                get_heating_demand(thermostat, heating_season, method="hourlysumHDD")

        # take first column
        hourly_runtime = thermostat.get_heating_columns()[0][heating_season]

        # run regressions
        slope_deltaT, intercept_deltaT, mean_sq_err_deltaT = runtime_regression(hourly_runtime, demand_deltaT)
        slope_dailyavgHDD, intercept_dailyavgHDD, mean_sq_err_dailyavgHDD = runtime_regression(hourly_runtime, demand_dailyavgHDD)
        slope_hourlysumHDD, intercept_hourlysumHDD, mean_sq_err_hourlysumHDD = runtime_regression(hourly_runtime, demand_hourlysumHDD)

        outputs["slope_deltaT"] = slope_deltaT
        outputs["slope_dailyavgHDD"] = slope_dailyavgHDD
        outputs["slope_hourlysumHDD"] = slope_hourlysumHDD

        outputs["intercept_deltaT"] = intercept_deltaT
        outputs["intercept_dailyavgHDD"] = intercept_dailyavgHDD
        outputs["intercept_hourlysumHDD"] = intercept_hourlysumHDD

        outputs["mean_squared_error_deltaT"] = mean_sq_err_deltaT
        outputs["mean_squared_error_dailyavgHDD"] = mean_sq_err_dailyavgHDD
        outputs["mean_squared_error_hourlysumHDD"] = mean_sq_err_hourlysumHDD

        actual_seasonal_runtime = thermostat.get_heating_season_total_runtime(heating_season)[0]
        n_days = heating_season.sum() / 24
        actual_daily_runtime = actual_seasonal_runtime / n_days

        outputs["actual_daily_runtime"] = actual_daily_runtime
        outputs["actual_seasonal_runtime"] = actual_seasonal_runtime

        demand_baseline_deltaT = get_heating_season_baseline_heating_demand(
                thermostat,heating_season,baseline_setpoints,method="deltaT")
        demand_baseline_dailyavgHDD = get_heating_season_baseline_heating_demand(
                thermostat,heating_season,baseline_setpoints,deltaT_base_est_dailyavgHDD,method="dailyavgHDD")
        demand_baseline_hourlysumHDD = get_heating_season_baseline_heating_demand(
                thermostat,heating_season,baseline_setpoints,deltaT_base_est_hourlysumHDD,method="hourlysumHDD")

        daily_avoided_runtime_deltaT = get_daily_avoided_runtime(slope_deltaT,demand_deltaT,demand_baseline_deltaT)
        daily_avoided_runtime_dailyavgHDD = get_daily_avoided_runtime(slope_dailyavgHDD,demand_dailyavgHDD,demand_baseline_dailyavgHDD)
        daily_avoided_runtime_hourlysumHDD = get_daily_avoided_runtime(slope_hourlysumHDD,demand_hourlysumHDD,demand_baseline_hourlysumHDD)

        baseline_seasonal_runtime_deltaT = \
                get_total_baseline_heating_runtime(thermostat,heating_season,daily_avoided_runtime_deltaT)
        baseline_seasonal_runtime_dailyavgHDD = \
                get_total_baseline_heating_runtime(thermostat,heating_season,daily_avoided_runtime_dailyavgHDD)
        baseline_seasonal_runtime_hourlysumHDD = \
                get_total_baseline_heating_runtime(thermostat,heating_season,daily_avoided_runtime_hourlysumHDD)

        outputs["baseline_seasonal_runtime_deltaT"] = baseline_seasonal_runtime_deltaT
        outputs["baseline_seasonal_runtime_dailyavgHDD"] = baseline_seasonal_runtime_dailyavgHDD
        outputs["baseline_seasonal_runtime_hourlysumHDD"] = baseline_seasonal_runtime_hourlysumHDD

        baseline_daily_runtime_deltaT = baseline_seasonal_runtime_deltaT / n_days
        baseline_daily_runtime_dailyavgHDD = baseline_seasonal_runtime_dailyavgHDD / n_days
        baseline_daily_runtime_hourlysumHDD = baseline_seasonal_runtime_hourlysumHDD / n_days

        outputs["baseline_daily_runtime_deltaT"] = baseline_daily_runtime_deltaT
        outputs["baseline_daily_runtime_dailyavgHDD"] = baseline_daily_runtime_dailyavgHDD
        outputs["baseline_daily_runtime_hourlysumHDD"] = baseline_daily_runtime_hourlysumHDD

        seasonal_savings_deltaT = get_seasonal_percent_savings(baseline_seasonal_runtime_deltaT,daily_avoided_runtime_deltaT)
        seasonal_savings_dailyavgHDD = get_seasonal_percent_savings(baseline_seasonal_runtime_dailyavgHDD,daily_avoided_runtime_dailyavgHDD)
        seasonal_savings_hourlysumHDD = get_seasonal_percent_savings(baseline_seasonal_runtime_hourlysumHDD,daily_avoided_runtime_hourlysumHDD)

        outputs["seasonal_savings_deltaT"] = seasonal_savings_deltaT
        outputs["seasonal_savings_dailyavgHDD"] = seasonal_savings_dailyavgHDD
        outputs["seasonal_savings_hourlysumHDD"] = seasonal_savings_hourlysumHDD

        seasonal_avoided_runtime_deltaT = daily_avoided_runtime_deltaT.sum()
        seasonal_avoided_runtime_dailyavgHDD = daily_avoided_runtime_dailyavgHDD.sum()
        seasonal_avoided_runtime_hourlysumHDD = daily_avoided_runtime_hourlysumHDD.sum()

        outputs["seasonal_avoided_runtime_deltaT"] = seasonal_avoided_runtime_deltaT
        outputs["seasonal_avoided_runtime_dailyavgHDD"] = seasonal_avoided_runtime_dailyavgHDD
        outputs["seasonal_avoided_runtime_hourlysumHDD"] = seasonal_avoided_runtime_hourlysumHDD

        n_days_both, n_days_incomplete = thermostat.get_season_ignored_days(season_name)

        outputs["n_days_both_heating_and_cooling"] = n_days_both
        outputs["n_days_incomplete"] = n_days_incomplete


        rhus = thermostat.get_resistance_heat_utilization(heating_season)
        if rhus is None:
            for low, high in [(i,i+5) for i in range(0,60,5)]:
                outputs["rhu_{:02d}F_to_{:02d}F".format(low,high)] = None
        else:
            for rhu, (low, high) in zip(rhus,[(i,i+5) for i in range(0,60,5)]):
                outputs["rhu_{:02d}F_to_{:02d}F".format(low,high)] = rhu

        seasonal_metrics[season_name] = outputs

    return seasonal_metrics

def seasonal_metrics_to_csv(seasonal_metrics,filepath):
    rows = []
    for season_name, metrics in seasonal_metrics.iteritems():
        rows.append(dict(metrics.items() + {"season": season_name}.items()))

    df = pd.DataFrame(rows)
    df.to_csv(filepath,index=False)
