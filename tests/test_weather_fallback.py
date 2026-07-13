import json as _json

import pytest
import pandas as pd
import pytz
import requests
from unittest.mock import patch, MagicMock

from thermostat.weather_fallback import fetch_ghcnh_hourly_temp_data


def _mock_response(json_data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    # iter_content used by the streaming implementation
    encoded = _json.dumps(json_data).encode("utf-8")
    mock.iter_content.return_value = iter([encoded])
    if status_code >= 400:
        mock.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "HTTP {}".format(status_code)
        )
    else:
        mock.raise_for_status.return_value = None
    return mock


_START = pd.Timestamp("2025-08-01", tz="UTC")
_END = pd.Timestamp("2025-08-03", tz="UTC")

_SAMPLE_RECORDS = [
    {"DATE": "2025-08-01T00:00:00", "temperature": "17.8"},
    {"DATE": "2025-08-01T01:00:00", "temperature": "16.5"},
    {"DATE": "2025-08-01T02:00:00", "temperature": "15.9"},
]


def test_normal_response_parsed_correctly():
    with patch("thermostat.weather_fallback.requests.get") as mock_get:
        mock_get.return_value = _mock_response(_SAMPLE_RECORDS)
        result = fetch_ghcnh_hourly_temp_data("23234", _START, _END)

    assert isinstance(result, pd.Series)
    assert result.index.tz == pytz.UTC
    assert len(result) == 3
    assert abs(result.iloc[0] - 17.8) < 0.01
    assert abs(result.iloc[1] - 16.5) < 0.01


def test_sub_hourly_records_resampled_to_hourly():
    records = [
        {"DATE": "2025-08-01T00:00:00", "temperature": "16.0"},
        {"DATE": "2025-08-01T00:30:00", "temperature": "18.0"},
        {"DATE": "2025-08-01T01:00:00", "temperature": "20.0"},
    ]
    with patch("thermostat.weather_fallback.requests.get") as mock_get:
        mock_get.return_value = _mock_response(records)
        result = fetch_ghcnh_hourly_temp_data("23234", _START, _END)

    assert len(result) == 2
    assert abs(result.iloc[0] - 17.0) < 0.01  # mean of 16.0 and 18.0
    assert abs(result.iloc[1] - 20.0) < 0.01


def test_network_error_returns_empty_series():
    with patch("thermostat.weather_fallback.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("unreachable")
        result = fetch_ghcnh_hourly_temp_data("23234", _START, _END)

    assert isinstance(result, pd.Series)
    assert len(result) == 0
    assert result.index.tz == pytz.UTC


def test_http_error_returns_empty_series():
    with patch("thermostat.weather_fallback.requests.get") as mock_get:
        mock_get.return_value = _mock_response([], status_code=500)
        result = fetch_ghcnh_hourly_temp_data("23234", _START, _END)

    assert isinstance(result, pd.Series)
    assert len(result) == 0


def test_empty_response_returns_empty_series():
    with patch("thermostat.weather_fallback.requests.get") as mock_get:
        mock_get.return_value = _mock_response([])
        result = fetch_ghcnh_hourly_temp_data("23234", _START, _END)

    assert isinstance(result, pd.Series)
    assert len(result) == 0


def test_station_id_format():
    with patch("thermostat.weather_fallback.requests.get") as mock_get:
        mock_get.return_value = _mock_response(_SAMPLE_RECORDS)
        fetch_ghcnh_hourly_temp_data("23234", _START, _END)

    call_kwargs = mock_get.call_args
    params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
    assert params["stations"] == "USW00023234"


def test_short_wban_id_zero_padded():
    with patch("thermostat.weather_fallback.requests.get") as mock_get:
        mock_get.return_value = _mock_response([])
        fetch_ghcnh_hourly_temp_data("1", _START, _END)

    call_kwargs = mock_get.call_args
    params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
    assert params["stations"] == "USW00000001"


def test_malformed_temperature_record_skipped():
    records = [
        {"DATE": "2025-08-01T00:00:00", "temperature": "not_a_number"},
        {"DATE": "2025-08-01T01:00:00", "temperature": "16.0"},
    ]
    with patch("thermostat.weather_fallback.requests.get") as mock_get:
        mock_get.return_value = _mock_response(records)
        result = fetch_ghcnh_hourly_temp_data("23234", _START, _END)

    assert len(result) == 1
    assert abs(result.iloc[0] - 16.0) < 0.01
