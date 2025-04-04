import os
from datetime import date

import pytest
from polygon.rest.models import DailyOpenCloseAgg

from app.polygon_cli import PolygonAPICli


def test_polygon_cli_with_no_api_key():
    # given
    old_api_key = os.environ.pop("POLYGON_API_KEY", None)
    assert os.environ.get("POLYGON_API_KEY") is None
    cli = PolygonAPICli()

    # raises
    with pytest.raises(
        ValueError, match="You must configure POLYGON_API_KEY in docker-compose.yaml."
    ):
        cli.client

    # teardown
    if old_api_key is not None:
        os.environ["POLYGON_API_KEY"] = old_api_key


def test_polygon_get_daily_open_close_agg(mock_polygon_get_daily_open_close_agg):
    # when
    day = date(2025, 4, 2)
    data = PolygonAPICli().get_daily_open_close_agg("AAPL", day)

    # then
    mock_polygon_get_daily_open_close_agg.assert_called_once_with(
        "AAPL", day.isoformat(), adjusted="true"
    )
    assert type(data) == DailyOpenCloseAgg
    assert data.__dict__ == {
        "after_hours": 207.91,
        "close": 223.89,
        "from_": "2025-04-02",
        "high": 225.19,
        "low": 221.02,
        "open": 221.315,
        "pre_market": 222.82,
        "status": "OK",
        "symbol": "AAPL",
        "volume": 35905904.0,
    }
