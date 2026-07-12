"""Tests for scripts/build_station_data.py."""

import struct
import tempfile
import os
from unittest.mock import patch
import pytest

from scripts.build_station_data import read_census_dbf, lookup_station


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_minimal_dbf(path, records):
    """Write a minimal dBASE III DBF with ZCTA5CE20, INTPTLAT20, INTPTLON20.

    records: list of (zcta_str, lat_str, lon_str)
    """
    fields = [
        (b'ZCTA5CE20\x00\x00', b'C', 5),
        (b'INTPTLAT20\x00', b'C', 11),
        (b'INTPTLON20\x00', b'C', 12),
    ]
    n_fields = len(fields)
    record_size = 1 + sum(f[2] for f in fields)  # 1 deletion flag + data
    header_bytes = 32 + n_fields * 32 + 1       # header + field descriptors + terminator

    with open(path, 'wb') as f:
        # Main header (32 bytes)
        f.write(struct.pack('<B', 3))           # version
        f.write(struct.pack('<BBB', 25, 1, 1))  # date y/m/d
        f.write(struct.pack('<I', len(records))) # nrecords
        f.write(struct.pack('<H', header_bytes))
        f.write(struct.pack('<H', record_size))
        f.write(b'\x00' * 20)                  # reserved

        # Field descriptors (32 bytes each)
        for name, ftype, flen in fields:
            fd = bytearray(32)
            fd[0:len(name)] = name
            fd[11] = ord(ftype)
            fd[16] = flen
            f.write(bytes(fd))

        f.write(b'\r')  # header terminator

        # Records
        for zcta, lat, lon in records:
            f.write(b' ')                              # deletion flag (space = active)
            f.write(zcta.ljust(5).encode('ascii'))
            f.write(lat.ljust(11).encode('ascii'))
            f.write(lon.ljust(12).encode('ascii'))

        f.write(b'\x1a')  # EOF marker


# ---------------------------------------------------------------------------
# Tests for read_census_dbf
# ---------------------------------------------------------------------------

def test_read_census_dbf_returns_correct_records():
    with tempfile.NamedTemporaryFile(suffix='.dbf', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        _write_minimal_dbf(tmp_path, [
            ('60601', '+41.8858900', '-087.6181700'),
            ('10001', '+40.7484400', '-073.9967100'),
        ])
        records = read_census_dbf(tmp_path)

        assert len(records) == 2
        assert records[0] == ('60601', pytest.approx(41.88589), pytest.approx(-87.61817))
        assert records[1] == ('10001', pytest.approx(40.74844), pytest.approx(-73.99671))
    finally:
        os.unlink(tmp_path)


def test_read_census_dbf_skips_deleted_records():
    with tempfile.NamedTemporaryFile(suffix='.dbf', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        fields = [
            (b'ZCTA5CE20\x00\x00', b'C', 5),
            (b'INTPTLAT20\x00', b'C', 11),
            (b'INTPTLON20\x00', b'C', 12),
        ]
        record_size = 1 + 5 + 11 + 12
        header_bytes = 32 + len(fields) * 32 + 1

        with open(tmp_path, 'wb') as f:
            f.write(struct.pack('<B', 3))
            f.write(struct.pack('<BBB', 25, 1, 1))
            f.write(struct.pack('<I', 2))
            f.write(struct.pack('<H', header_bytes))
            f.write(struct.pack('<H', record_size))
            f.write(b'\x00' * 20)
            for name, ftype, flen in fields:
                fd = bytearray(32)
                fd[0:len(name)] = name
                fd[11] = ord(ftype)
                fd[16] = flen
                f.write(bytes(fd))
            f.write(b'\r')
            # First record: deleted
            f.write(b'*')
            f.write(b'60601' + b'+41.8858900' + b'-087.6181700')
            # Second record: active
            f.write(b' ')
            f.write(b'10001' + b'+40.7484400' + b'-073.9967100')
            f.write(b'\x1a')

        records = read_census_dbf(tmp_path)
        assert len(records) == 1
        assert records[0][0] == '10001'
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Tests for lookup_station
# ---------------------------------------------------------------------------

def test_lookup_station_returns_station_when_found():
    with patch('scripts.build_station_data._get_both_year_station', return_value='725300'):
        zcta, station = lookup_station(('60601', 41.88, -87.63))
    assert zcta == '60601'
    assert station == '725300'


def test_lookup_station_returns_none_when_not_found():
    with patch('scripts.build_station_data._get_both_year_station', return_value=None):
        zcta, station = lookup_station(('96801', 21.30, -157.85))
    assert zcta == '96801'
    assert station is None


def test_lookup_station_returns_none_on_exception():
    with patch('scripts.build_station_data._get_both_year_station', side_effect=RuntimeError('oops')):
        zcta, station = lookup_station(('00000', 0.0, 0.0))
    assert station is None
