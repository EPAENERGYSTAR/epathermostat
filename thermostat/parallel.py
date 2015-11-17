import pandas as pd
from eemeter.location import _load_zipcode_to_station_index

from collections import defaultdict
from itertools import cycle
from zipfile import ZipFile
import tempfile
import os

def schedule_batches(metadata_filename, n_batches, zip_files=False, batches_dir=None):
    """ Batch scheduler for large sets of thermostats. Can either create
    zipped directories ready be sent to separate processors for parallel
    processing, or unpackaged metadata dataframes for more flexible processing.

    Parameters
    ----------
    metadata_filename : str
        Full path to location of file containing CSV formatted metadata for
    n_batches : int
        Number of batches desired. Should be <= the number of available
        thermostats.
    zip_files : boolean
        If True, create zipped directories of metadata and interval data. Each
        batch will be named batch_XXXXX.zip, and will contain a directory named
        `data`, which contains metadata and interval data for the batch. Must
        supply `batches_dir` argument to use this option.
    batches_dir : str
        Path to directory in which to save created batches. Ignored for
        zip_files=False.


    Returns
    -------
    batches : list of str or list of pd.DataFrame
        If zip_files is True, then returns list of names of created zip files.
        Otherwise, returns list of metadata dataframes containing batches.

    """

    if zip_files:
        if batches_dir is None:
            message = "Cannot have batches_dir==None when zip_files==True. " \
                    "Please supply a directory in which to save batches."
            raise ValueError(message)

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

    if zip_files:

        if not os.path.exists(batches_dir):
            os.makedirs(batches_dir)

        batch_zipfile_names = []
        for i, batch_df in enumerate(batch_dfs):

            batch_name = "batch_{:05d}.zip".format(i)
            batch_zipfile_name = os.path.join(batches_dir, batch_name)
            batch_zipfile_names.append(batch_zipfile_name)

            _, fname = tempfile.mkstemp()
            batch_df.to_csv(fname, index=False)

            with ZipFile(batch_zipfile_name, 'w') as batch_zip:
                batch_zip.write(fname, arcname=os.path.join('data', 'metadata.csv'))

                for filename in batch_df.interval_data_filename:
                    interval_data_source = os.path.join(os.path.dirname(metadata_filename), filename)
                    batch_zip.write(interval_data_source, arcname=os.path.join('data', filename))

        return batch_zipfile_names

    else:
        return batch_dfs

def _get_batch_sizes(n_rows, n_batches):
    n_base = int(n_rows / n_batches)
    remainder = (n_rows % n_batches)
    return [n_base + int(i < remainder) for i in range(n_batches)]
