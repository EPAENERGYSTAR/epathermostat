import pandas as pd
from eemeter.location import _load_zipcode_to_station_index

from collections import defaultdict
from itertools import cycle

def schedule_batches(metadata_filename, n_batches, zip_files=False):
    metadata_df = pd.read_csv(metadata_filename, dtype={"zipcode": str})
    index = _load_zipcode_to_station_index()
    stations = [index[zipcode] for zipcode in metadata_df.zipcode]

    n_rows = metadata_df.shape[0]


    # group rows by stations then order groups by number of stations.
    rows_by_station = defaultdict(list)
    for station, (i, row) in zip(stations, metadata_df.iterrows()):
        rows_by_station[station].append(row)

    ordered_rows = [rows_by_station[i[0]] for i in sorted([ (s, len(rs))
            for s, rs in rows_by_station.items()], key=(lambda x: x[1]))]

    # iterate over row groups, greedily adding contents to batches

    batches = [[] for i in range(n_batches)]

    batch_sizes = _get_batch_sizes(n_rows, n_batches)

    current_batch = cycle(range(n_batches))


    for rows in ordered_rows:
        n_rows = len(rows)
        n_rows_taken = 0
        while n_rows_taken < n_rows:
            batch_i = next(current_batch)
            target_batch_size = batch_sizes[batch_i]
            batch = batches[batch_i]
            space_left = target_batch_size - len(batch)
            rows_to_add = rows[n_rows_taken:n_rows_taken + space_left]
            n_rows_taken += len(rows_to_add)
            batch.extend(rows_to_add)

    batch_dfs = [pd.DataFrame(rows) for rows in batches]

    return batch_dfs

def _get_batch_sizes(n_rows, n_batches):
    n_base = int(n_rows / n_batches)
    remainder = (n_rows % n_batches)
    return [n_base + int(i < remainder) for i in range(n_batches)]
