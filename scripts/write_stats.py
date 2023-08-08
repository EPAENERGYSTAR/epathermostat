# for testing purposes; only run the first n thermostat files
# set to None to run all
top_n = 30


import os
from thermostat.importers import from_csv, get_single_thermostat
from thermostat.exporters import metrics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

def main():
    # path to the raw thermostat data in csv format
    data_dir = os.path.join('../', '../', 'tau-search-2', 'EPA_Tau')
    metadata_path = os.path.join(data_dir, '2019_epa_tau.csv')
    # dir to save tau search stats to (multiple files per thermostat)
    output_dir = os.path.join('../', '../', 'tau-search-2', 'EPA_Tau_results')
    METRICS_FILEPATH = os.path.join(output_dir, '2019_EPA_tau_2023_06_01_metrics_new.csv')

    thermostats, tstat_errors = from_csv(metadata_path, top_n=top_n)
    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

    metrics_to_csv(metrics, METRICS_FILEPATH)

if __name__=='__main__':
    main()