#!/usr/bin/env python
# coding: utf-8

# ## Export missing data results
# Takes the results of the missing-data "gremlin" code that randomly removes chunks of data and plots the impact. 
# 
# Output is one charts for heating and one for cooling season, with subplots for every climate zone. Plots are box-and-whisker distribution of change to the savings across the population when only X% of core days remain. 
# 
# Expected result is that there is no change in savings when 100% of core days are present (by definition). As more data is missing (smaller percent of core days)

# In[57]:


import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
# import seaborn as sns


# In[4]:


con = sqlite3.connect("metrics.db")


# In[5]:


metrics = pd.read_sql_query("""
SELECT * from metric
""", con)
# metrics.head()


# In[6]:


best_metrics = metrics.query('days_removed==0').set_index('ct_identifier')    .loc[:,['percent_savings_baseline_percentile', 
             'baseline_percentile_core_cooling_comfort_temperature',
             'baseline_percentile_core_heating_comfort_temperature',
             'n_core_cooling_days',
             'n_core_heating_days',
             'heating_or_cooling']]


# In[25]:


def round_five_pct(decimal):
    fifth_pct = decimal * 20
    fifth_pct = round(fifth_pct, 0)
    return fifth_pct * 5


# In[29]:


metrics_w_best = metrics.merge(best_metrics, on=['ct_identifier', 'heating_or_cooling'], how='inner', suffixes=['','_best'])

metrics_w_best['percent_savings_baseline_percentile_change'] = metrics_w_best.percent_savings_baseline_percentile     - metrics_w_best.percent_savings_baseline_percentile_best

metrics_w_best['baseline_percentile_core_cooling_comfort_temperature_change'] = metrics_w_best.baseline_percentile_core_cooling_comfort_temperature     - metrics_w_best.baseline_percentile_core_cooling_comfort_temperature_best

metrics_w_best['baseline_percentile_core_heating_comfort_temperature_change'] = metrics_w_best.baseline_percentile_core_heating_comfort_temperature     - metrics_w_best.baseline_percentile_core_heating_comfort_temperature_best

metrics_w_best['n_core_cooling_days_change'] = metrics_w_best.n_core_cooling_days     - metrics_w_best.n_core_cooling_days_best

metrics_w_best['n_core_heating_days_change'] = metrics_w_best.n_core_heating_days     - metrics_w_best.n_core_heating_days_best

metrics_w_best['n_core_cooling_days_percent'] = round_five_pct(metrics_w_best.n_core_cooling_days     / metrics_w_best.n_core_cooling_days_best)

metrics_w_best['n_core_heating_days_percent'] = round_five_pct(metrics_w_best.n_core_heating_days     / metrics_w_best.n_core_heating_days_best)

# metrics_w_best.sort_values(by=['ct_identifier', 'heating_or_cooling', 'days_removed'])[['ct_identifier', 'heating_or_cooling', 'days_removed']].head(15)


# In[30]:


# metrics_w_best[['ct_identifier', 'n_core_heating_days', 'n_core_heating_days_change', 'n_core_heating_days_percent', 'n_core_heating_days_best']]


# In[54]:


# Plot change in heating/cooling metric vs. core days
# Takes df with each tstat's "best" score (i.e. score with no missing days)
# and all the scores calculated with artificially-degraded data
# that has successively more days randomly removed

def plot_metric_change_vs_missing_days(metrics_w_best, heating_or_cooling):
    if heating_or_cooling not in ('heating', 'cooling'):
        print('value of heating_or_cooling must be one of "heating" or "cooling"')
    else:
        fig = metrics_w_best.query(f'days_removed<370 & heating_or_cooling=="{heating_or_cooling}_ALL"')                            .groupby('climate_zone')                            .boxplot(column=['percent_savings_baseline_percentile_change'], 
                                      layout=(5,1),
                                      by=f'n_core_{heating_or_cooling}_days_percent', figsize=[20,40],rot=90,
                                      showmeans=False)

        tick_spacing = 2
        for i, ax in fig.iteritems():
            ax.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
            ax.set_ylabel('Change in percent savings')
            ax.set_ylim(-20, 20)
            ax.set_xlim(0, 22)
        plt.savefig(f'change_in_{heating_or_cooling}_savings_vs_core_days.png')
        plt.show()


# In[55]:


plot_metric_change_vs_missing_days(metrics_w_best, 'heating')


# In[56]:


plot_metric_change_vs_missing_days(metrics_w_best, 'cooling')


# In[ ]:




