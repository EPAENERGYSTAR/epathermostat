#!/usr/bin/env python
import csv
import glob
from pathlib import Path

from datetime import datetime, timedelta

FIELDNAMES = [
        "thermostat_id",
        "heat_type",
        "heat_stage",
        "cool_type",
        "cool_stage",
        "zipcode",
        "utc_offset",
        "interval_data_filename",
        ]

EQUIPMENT_MAPPING = [
        {'heat_type': None, 'heat_stage': 'two_stage', 'cool_type': None, 'cool_stage': 'two_stage'},  # 0
        {'heat_type': 'heat_pump_electric_backup', 'heat_stage': 'single_stage', 'cool_type': 'heat_pump', 'cool_stage': None},  # 1
        {'heat_type': 'heat_pump_no_electric_backup', 'heat_stage': 'single_stage', 'cool_type': 'heat_pump', 'cool_stage': None},  # 2
        {'heat_type': 'non_heat_pump', 'heat_stage': 'single_stage', 'cool_type': 'central', 'cool_stage': 'single_stage'},  # 3
        {'heat_type': 'non_heat_pump', 'heat_stage': 'single_stage', 'cool_type': 'none', 'cool_stage': None},  # 4
        {'heat_type': 'none', 'heat_stage': None, 'cool_type': 'central', 'cool_stage': 'single_stage'},  # 5
        ]

# "thermostat_id,equipment_type,zipcode,utc_offset,interval_data_filename"

def main():
    """ This script is for converting over metadata files to the new format for
    EPAThermostat 2.0. It should be used for testing old data files, and is not
    recommended for data submission.

    """

    for filename in glob.iglob('metadata*.csv'):
        input_filename = filename
        output_filename = Path("new") / filename
        with open(output_filename, 'w') as outfile:
            csv_out = csv.DictWriter(outfile, FIELDNAMES)
            csv_out.writeheader()

            with open(input_filename) as csvfile:
                metadata_csv = csv.DictReader(csvfile)
                for row in metadata_csv:
                    current_row = {}
                    current_row['thermostat_id'] = row['thermostat_id']
                    equipment_type = EQUIPMENT_MAPPING[int(row['equipment_type'])]
                    current_row['heat_type'] = equipment_type['heat_type']
                    current_row['cool_type'] = equipment_type['cool_type']
                    current_row['heat_stage'] = equipment_type['heat_stage']
                    current_row['cool_stage'] = equipment_type['cool_stage']

                    current_row['zipcode'] = row['zipcode']
                    current_row['utc_offset'] = row['utc_offset']
                    current_row['interval_data_filename'] = row['interval_data_filename']
                    csv_out.writerow(current_row)


if __name__ == '__main__':
    main()
