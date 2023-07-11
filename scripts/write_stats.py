import os
import pandas as pd
import eeweather
from thermostat.core import Thermostat
from thermostat.climate_zone import retrieve_climate_zone
from thermostat.importers import from_csv, get_single_thermostat
from thermostat.exporters import metrics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

def main():
    data_dir = os.path.join('../', '../', 'tau-search-2', 'EPA_Tau')
    metadata_path = os.path.join(data_dir, '2019_epa_tau.csv')
    output_dir = os.path.join('../', '../', 'tau-search-2', 'EPA_Tau_results')
    METRICS_FILEPATH = os.path.join(output_dir, '2019_EPA_tau_2023_06_01_metrics_new.csv')
    # metadata = pd.read_csv(metadata_path)
    # metadata.zipcode = metadata.zipcode.astype(str)
    # metadata.head()

    thermostats, tstat_errors = from_csv(metadata_path, top_n=None)
    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

    metrics_to_csv(metrics, METRICS_FILEPATH)

if __name__=='__main__':
    main()