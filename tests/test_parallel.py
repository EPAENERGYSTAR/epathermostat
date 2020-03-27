from thermostat.parallel import schedule_batches
from thermostat.equipment_type import EQUIPMENT_MAPPING

import os
import tempfile
import zipfile
from uuid import uuid4

import numpy as np
import pandas as pd
from scipy.stats import randint
import random

import pytest

@pytest.fixture
def metadata_filename():
    columns = [
        "thermostat_id",
        'heat_type',
        'heat_stage',
        'cool_type',
        'cool_stage',
        "zipcode",
        "utc_offset",
        "interval_data_filename",
    ]

    n_thermostats = 100
    thermostat_ids = [uuid4() for i in range(n_thermostats)]
    equipment_types =  [random.randint(0, 5) for i in range(n_thermostats)]
    heat_type = [EQUIPMENT_MAPPING[x]['heat_type'] for x in equipment_types]
    heat_stage = [EQUIPMENT_MAPPING[x]['heat_stage'] for x in equipment_types]
    cool_type = [EQUIPMENT_MAPPING[x]['cool_type'] for x in equipment_types]
    cool_stage = [EQUIPMENT_MAPPING[x]['cool_stage'] for x in equipment_types]
    zipcodes = [
        "70754", "70722", "70726", "70449", "70442", # "722312" 50
        "70443", "70441", "70446", "70447", "70444", # "722312"
        "70836", "70778", "70770", "70774", "70777", # "722312"
        "70433", "70437", "70436", "70435", "70438", # "722312"
        "70744", "70748", "70462", "70465", "70466", # "722312"
        "70791", "70714", "70711", "70451", "70450", # "722312"
        "70453", "70455", "70454", "70456", "70809", # "722312"
        "70806", "70807", "70805", "70769", "70761", # "722312"
        "70402", "70403", "70401", "70737", "70730", # "722312"
        "70733", "70739", "70785", "70789", "70706", # "722312"
        "45341", "45344", "45349", "45319", "45434", # "745700" 55
        "60018", "60191", "60193", "60195", "60194", # "725300" 60
        "97473", "97449", "97493", "97467", "97459", # "726917" 65
        "60421", "60544", "60404", "60408", "60481", # "725345" 70
        "36590", "36564", "36606", "36605", "36532", # "722235" 75
        "36541", "36544", "36568", "36608", "36609", # "722230" 80
        "23106", "23060", "23229", "23222", "23294", # "724029" 85
        "13674", "13601", "13606", "13605", "13682", # "726227" 90
        "12978", "12972", "12985", "12903", "12901", # "726225" 95
        "61051", # "725326" 96
        "76207", # "722589" 97
        "36362", # "722239" 98
        "57233", # "726546" 99
        "56289", # "726547" 100
    ]
    utc_offsets = [-7 for _ in range(n_thermostats)]
    interval_data_filenames = ["thermostat_{}.csv".format(i) for i in thermostat_ids]

    df = pd.DataFrame({
        "thermostat_id": thermostat_ids,
        "heat_type": heat_type,
        "heat_stage": heat_stage,
        "cool_type": cool_type,
        "cool_stage": cool_stage,
        "zipcode": zipcodes,
        "utc_offset": utc_offsets,
        "interval_data_filename": interval_data_filenames,
    }, columns=columns)


    temp_dir = tempfile.mkdtemp()
    metadata_filename = os.path.join(temp_dir, "metadata.csv")
    df.to_csv(metadata_filename, index=False)

    for interval_data_filename in df.interval_data_filename:
        fname = os.path.join(temp_dir, interval_data_filename)
        with open(fname, 'w') as f :
            f.write("INTERVAL DATA FILE CONTENT")

    return metadata_filename

def test_schedule_batches_metadata_only(metadata_filename):

    batches = schedule_batches(metadata_filename, 5)

    assert len(batches) == 5
    assert sum([len(b) for b in batches]) == 100
    assert isinstance(batches[0], pd.DataFrame)

def test_schedule_batches_zip_files(metadata_filename):

    with pytest.raises(ValueError):
        schedule_batches(metadata_filename, 5, True)

    temp_dir = tempfile.mkdtemp()
    batch_zipfile_names = schedule_batches(metadata_filename, 5, True, temp_dir)

    assert len(batch_zipfile_names) == 5
    assert isinstance(batch_zipfile_names[0], str)

    with zipfile.ZipFile(batch_zipfile_names[0]) as zf:
        assert len(zf.infolist()) == 21
