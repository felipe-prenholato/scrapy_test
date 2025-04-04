import json
from decimal import Decimal

import pytest
from sqlmodel import select

from app.main import REDIS_CACHE_KEY
from app.models import Stock


def test_get_stock(test_client, db, redis, mock_polygon_get_daily_open_close_agg):
    stock_symbol = "AAPL"

    # Stock shouldn't exist yet
    stock = db.exec(
        select(Stock).where(Stock.company_code == stock_symbol)
    ).one_or_none()
    assert stock is None
    assert redis.get(REDIS_CACHE_KEY.format(symbol=stock_symbol)) is None

    # request info
    response = test_client.get(f"/stock/{stock_symbol}")
    stock_data = response.json()

    # check few fields
    assert stock_data["company_name"] == "Apple Inc."
    assert stock_data["performance_data"]["five_days"] == 1.07
    assert stock_data["stock_values"]["open"] == 221.315
    assert stock_data["competitors"][0]["name"] == "Microsoft Corp."

    # check cache
    cached = json.loads(redis.get(REDIS_CACHE_KEY.format(symbol=stock_symbol)).decode())
    assert cached == stock_data

    # second request should hit cache, and not mock_polygon_get_daily_open_close_agg
    response2 = test_client.get(f"/stock/{stock_symbol}")
    assert response2.json() == stock_data
    assert mock_polygon_get_daily_open_close_agg.call_count == 1


@pytest.mark.usefixtures("mock_polygon_get_daily_open_close_agg")
def test_update_stock(test_client, db):
    stock_symbol = "AAPL"

    # Stock shouldn't exist yet
    stock = db.exec(
        select(Stock).where(Stock.company_code == stock_symbol)
    ).one_or_none()
    assert stock is None

    # first request
    response = test_client.post(f"/stock/{stock_symbol}", json={"amount": "5.33"})
    assert response.status_code == 201, response.text

    # stock should have id and purchased_amount
    stock = db.exec(
        select(Stock).where(Stock.company_code == stock_symbol)
    ).one_or_none()
    assert stock.id > 0
    assert stock.purchased_amount == Decimal("5.33")

    # second request
    response = test_client.post(f"/stock/{stock_symbol}", json={"amount": "5.33"})
    assert response.status_code == 201, response.text

    # stock should have updated purchased_amount
    db.refresh(stock)
    assert stock.purchased_amount == Decimal("10.66")
