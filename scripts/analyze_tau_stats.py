import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

""""
DIRECTIONS
in thermostats/core.py, set the variable "save_tau_stats" to True
in scripts/write_stats.py
    set the data_dir path to the location of the raw csv data
    set the metadata_path
    set the output_dir to a new location (don't overwrite your old outputs!)
    set top_n to None if you want to run the full batch, or keep it set to a small number for testing
run scripts/write_stats.py (takes a while)
in scripts/analyze_tau_stats.py
    set the data_dir path to the location of the raw csv data
    set results_old_path to the location of the old (pre tau-friendly) metrics file
    set results_path to match the METRICS_FILEPATH in write_stats.py
run scripts/analyze_tau_stats.py
look in tau_stats_plots directory for the plots and comparison csv file
"""


debug = False
# configure paths
#################
# path to directory of raw csv files in EPAthermostat-compatible format
data_dir = os.path.join('../', '../', 'tau-search-2', 'EPA_Tau')

# path to prior metrics file to use for comparison; should contain the same set of ct_identifiers
results_dir = os.path.join('../', '../', 'tau-search-2', 'EPA_Tau_results')
results_old_path = os.path.join(results_dir, '2019_EPA_tau_2022-11-03_metrics_base.csv')

# path to new results from experimental tau search code, same as METRICS_FILEPATH in write_stats.py
results_path = os.path.join(results_dir, '2019_EPA_tau_2023_06_01_metrics_new.csv')

# path to directory of stats files output from running tau search code; called "tau_search_path" in core.py module
stats_dir = 'tau_search_stats'

# path to directory where output plots and tables will be saved
plots_dir = 'tau_stats_plots'


def get_stats(ct_id, heat_or_cool, stats_dir=stats_dir):
    stats_path = os.path.join(stats_dir, f'{ct_id}_{heat_or_cool}_tau_search.csv')
    stats = pd.read_csv(stats_path)
    return stats


def get_raw_data(ct_id, data_dir=data_dir):
    data_path = os.path.join(data_dir, f'{ct_id}.csv')
    data = pd.read_csv(data_path)
    return data


def get_daily_data(ct_id, heat_or_cool, stats_dir=stats_dir):
    daily_data = {}
    dd_data_path = os.path.join(stats_dir, f'{ct_id}_{heat_or_cool}_dd.csv')
    rt_data_path = os.path.join(stats_dir, f'{ct_id}_{heat_or_cool}_run_time.csv')
    daily_data['degree_day'] = pd.read_csv(dd_data_path, usecols=[1]).iloc[:,0].to_numpy()
    daily_data['run_time'] = pd.read_csv(rt_data_path, usecols=[1]).iloc[:,0].to_numpy()
    return daily_data


def plot_regression(x_arr, y_arr, tau, alpha, ax, heat_or_cool='cool'):
        point_style = 'bo' if heat_or_cool=='cool' else 'ro'
        line_style = 'm-' if heat_or_cool=='cool' else 'g-'
        ax.plot(x_arr, y_arr, point_style)
        ax.plot(x_arr, np.full(len(x_arr), 0), 'k-')
        ax.plot(x_arr, np.array(alpha)*x_arr, line_style)
        ax.set_title(f'tau: {tau}, alpha: {alpha:.2f}')
        ax.set_ylabel('runtime (minutes)')
        if heat_or_cool == 'heat':
            ax.invert_xaxis()
            ax.set_xlabel('degree-days (reversed)')
        else:
            ax.set_xlabel('degree-days')
            
            
def get_runtime(ct_id, heat_or_cool, stats_dir=stats_dir):
    runtime_path = os.path.join(stats_dir, f'{ct_id}_{heat_or_cool}_run_time.csv')
    if os.path.exists(runtime_path):
        runtime = pd.read_csv(runtime_path)
        runtime.columns = ['date', f'{heat_or_cool}_runtime']
        runtime[f'{heat_or_cool}_runtime'].fillna(0, inplace=True)
    else:
        runtime = None
    return runtime


def get_all_runtime(ct_id, stats_dir=stats_dir):
    cool_runtime = get_runtime(ct_id, 'cool', stats_dir=stats_dir)
    heat_runtime = get_runtime(ct_id, 'heat', stats_dir=stats_dir)
    if cool_runtime is None and heat_runtime is None:
        return None
    if cool_runtime is None:
        all_runtime = heat_runtime
        all_runtime['cool_runtime'] = 0
    if heat_runtime is None:
        all_runtime = cool_runtime
        all_runtime['heat_runtime'] = 0
    if cool_runtime is not None and heat_runtime is not None:
        all_runtime = cool_runtime.merge(heat_runtime, on='date', how='outer')
    all_runtime.loc[:, ['heat_runtime', 'cool_runtime']] = all_runtime.loc[:, ['heat_runtime', 'cool_runtime']].fillna(0)
    all_runtime['runtime'] = all_runtime.cool_runtime + all_runtime.heat_runtime
    return all_runtime


def get_delta_t(ct_id, stats_dir=stats_dir):
    delta_t_path = os.path.join(stats_dir, f'{ct_id}_delta_t_daily_mean.csv')
    delta_t = pd.read_csv(delta_t_path)
    delta_t.columns = ['date', 'delta_t']
    return delta_t


def get_raw_daily_data(ct_id, stats_dir=stats_dir):
    all_runtime = get_all_runtime(ct_id, stats_dir=stats_dir)
    delta_t = get_delta_t(ct_id, stats_dir=stats_dir)
    daily_data = all_runtime.merge(delta_t, on='date', how='inner')
    return daily_data



def plot_raw_delta_t(ct_id, ax=None, results_old=None, results_new=None):
    if ax is None:
        fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(10,5));
    if results_old is None:
        results_old = pd.read_csv(results_old_path)
    if results_new is None:
        results_new = pd.read_csv(results_path) 
    
    ct_stats = {}
    raw_data = get_raw_data(ct_id)
    all_runtime = get_all_runtime(ct_id)
    delta_t = get_delta_t(ct_id)
    daily_data = all_runtime.merge(delta_t, on='date', how='inner')

    try:
        old_stats_cool = results_old.query("(ct_identifier==@ct_id) & (heating_or_cooling=='cooling_ALL')").iloc[0]
        core_stats_cool = results.query("(ct_identifier==@ct_id) & (heating_or_cooling=='cooling_ALL')").iloc[0]
        has_cool = True
    except:
        has_cool = False
    try:
        old_stats_heat = results_old.query("(ct_identifier==@ct_id) & (heating_or_cooling=='heating_ALL')").iloc[0]
        core_stats_heat = results.query("(ct_identifier==@ct_id) & (heating_or_cooling=='heating_ALL')").iloc[0]
        has_heat = True
    except:
        has_heat = False
    
    if has_cool:
        stats_cool = get_stats(ct_id, 'cool').query("is_best_tau").iloc[0]
        cooling_indoor_temp = raw_data.query("cool_runtime_stg1>0").temp_in.mean()
        cool_data = daily_data.query("cool_runtime > 0")
        
        ct_stats['old_tau_cool'] = old_stats_cool.tau
        ct_stats['tau_cool'] = stats_cool.tau
        ct_stats['old_alpha_cool'] = old_stats_cool.alpha
        ct_stats['alpha_cool'] = stats_cool.alpha
        ct_stats['old_metric_cool'] = old_stats_cool.percent_savings_baseline_percentile
        ct_stats['metric_cool'] = core_stats_cool.percent_savings_baseline_percentile
        ct_stats['old_cvrmse_cool'] = old_stats_cool.cv_root_mean_sq_err
        ct_stats['cvrmse_cool'] = (stats_cool.sq_errors ** 0.5) / cool_data.cool_runtime.mean()
        
    if has_heat:
        stats_heat = get_stats(ct_id, 'heat').query("is_best_tau").iloc[0]
        heating_indoor_temp = raw_data.query("heat_runtime_stg1>0").temp_in.mean()
        heat_data = daily_data.query("heat_runtime > 0")
        
        ct_stats['old_tau_heat'] = old_stats_heat.tau
        ct_stats['tau_heat'] = stats_heat.tau
        ct_stats['old_alpha_heat'] = old_stats_heat.alpha
        ct_stats['alpha_heat'] = stats_heat.alpha
        ct_stats['old_metric_heat'] = old_stats_heat.percent_savings_baseline_percentile
        ct_stats['metric_heat'] = core_stats_heat.percent_savings_baseline_percentile
        ct_stats['old_cvrmse_heat'] = old_stats_heat.cv_root_mean_sq_err
        ct_stats['cvrmse_heat'] = (stats_heat.sq_errors ** 0.5) / heat_data.heat_runtime.mean()

    if has_cool:
        daily_data.query("cool_runtime > 0").plot(kind='scatter', x='delta_t', y='cool_runtime', c='blue', alpha=0.5, 
                                                   ylim=(0,daily_data.runtime.max()+50), ax=ax);
        ax.plot(cool_data.delta_t, (cool_data.delta_t + stats_cool.tau) * stats_cool.alpha, 'b-', alpha=0.6);
        ax.plot(cool_data.delta_t, (cool_data.delta_t + old_stats_cool.tau) * old_stats_cool.alpha, 'b--', alpha=0.6);
    if has_heat:
        daily_data.query("heat_runtime > 0").plot(kind='scatter', x='delta_t', y='heat_runtime', c='red', ax=ax, alpha=0.5);
        ax.plot(heat_data.delta_t, (heat_data.delta_t + stats_heat.tau) * stats_heat.alpha * -1, 'r-', alpha=0.6);
        ax.plot(heat_data.delta_t, (heat_data.delta_t + old_stats_heat.tau) * old_stats_heat.alpha * -1, 'r--', alpha=0.6);
    return ct_stats




def generate_plots(ct_ids, plots_dir=plots_dir, results_old=None):
    if results_old is None:
        results_old = pd.read_csv(results_old_path)
    ct_data_list = []
    plt.rcParams['font.size'] = 10
    for ct_id in ct_ids[:]:
        fig, ax = plt.subplots(ncols=2, nrows=3, figsize=(20,15));
        for heat_or_cool in ['heat', 'cool']:
            ax_offset = 0 if heat_or_cool == 'cool' else 1
            h_c_label = f'{heat_or_cool}ing_ALL'
            ct_results = results_old.query("ct_identifier==@ct_id & heating_or_cooling==@h_c_label")
            if len(ct_results) == 0:
                   print(f'No results found for ct_id {ct_id} with {heat_or_cool}')
            else:
                try:
                    stats = get_stats(ct_id, heat_or_cool)
                except FileNotFoundError:
                    print(f'No stats for {ct_id} with {heat_or_cool}')
                    continue
                daily_data = get_daily_data(ct_id, heat_or_cool)
                old_tau = ct_results.iloc[0].tau
                old_alpha = ct_results.iloc[0].alpha
                best_tau = stats[stats.is_best_tau].tau.iloc[0]
                best_alpha = stats[stats.is_best_tau].alpha.iloc[0]
                best_sq_errors = stats[stats.is_best_tau].sq_errors.iloc[0]
                root_mean_sq_err = best_sq_errors ** 0.5
                cv_root_mean_sq_err = root_mean_sq_err / pd.Series(daily_data['run_time']).mean()
                ct_data_list.append({'ct_identifier': ct_id, 
                                     'heating_or_cooling': h_c_label, 
                                     'tau': best_tau, 
                                     'alpha': best_alpha, 
                                     'mean_sq_err': best_sq_errors,
                                     'cv_root_mean_sq_err': cv_root_mean_sq_err})

                ax_left = ax[ax_offset, 0]
                ax_right = ax[ax_offset, 1]
                stats.plot(x='tau', y='alpha', ax=ax_left, title=f'{ct_id} - {heat_or_cool}');
                stats.plot(x='tau', y='sq_errors', ax=ax_left, secondary_y = True);
                ax_left.axvline(best_tau, color="green", linestyle="dashed");
                ax_left.axvline(old_tau, color="grey", linestyle="dashed");
                ax_left.plot(old_tau, old_alpha, marker="o", markersize=10, markerfacecolor="blue")

                plot_regression(daily_data['degree_day'], daily_data['run_time'], best_tau, best_alpha, ax_right, heat_or_cool)
        ct_stats = plot_raw_delta_t(ct_id, ax[2, 0], results_old)
        # insert a table of text stats
        table_text = []
        table_text.append(['', 'old', 'new'])
        for stat in ['tau', 'alpha', 'metric', 'cvrmse']:
            for h_or_c in ['cool', 'heat']:
                key = f'{stat}_{h_or_c}'
                old_key = f'old_{stat}_{h_or_c}'
                if key in ct_stats.keys():
                    table_text.append([f'{stat} ({h_or_c})', f'{ct_stats[old_key]:.2f}', f'{ct_stats[key]:.2f}'])
        stats_table = ax[2, 1].table(table_text, loc='center')
        stats_table.auto_set_font_size(False)
        stats_table.set_fontsize(16)
        stats_table.scale(1,2)
        ax[2, 1].axis('off')

        plot_path = f'{ct_id}_plots.png'
        if debug:
            print(f'Saving to {plot_path}')
        plt.savefig(os.path.join(plots_dir, plot_path))
        plt.close()

    results_new = pd.DataFrame(ct_data_list)
    results_compared = results_old[['ct_identifier', 'heating_or_cooling', 'tau', 'alpha', 
                                    'cv_root_mean_sq_err', 'percent_savings_baseline_percentile', 'climate_zone']]\
        .merge(results_new, how='inner', on=['ct_identifier', 'heating_or_cooling'], suffixes=['_old', '_new'])
    return results_compared


if __name__ == '__main__':
    results_old = pd.read_csv(results_old_path)
    results = pd.read_csv(results_path)
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
    ct_ids = results.ct_identifier.unique()
    print('length of ct ids', len(ct_ids))
    results_compared = generate_plots(ct_ids, results_old=results_old)
    results_compared.to_csv(os.path.join(plots_dir, 'results_compared.csv'))