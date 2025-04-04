import logging
import os
from datetime import datetime, timedelta

# from app.redis_cache import get_cached_stock, set_cached_stock
from decimal import Decimal

from fastapi import Body, Depends, FastAPI, status
from sqlmodel import Session, select
from starlette.responses import JSONResponse, Response

from app.databases import (
    create_pg_db_and_tables,
    get_db,
    get_redis,
)
from app.marketwatch_cli import MwLxmlCli
from app.models import Stock
from app.polygon_cli import PolygonAPICli

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# SessionDep = Annotated[Session, Depends(get_pg_session)]
app = FastAPI()

REDIS_CACHE_KEY = "stocks_{symbol}"
SUPPORTED_SYMBOLS = ["AAPL", "AMZN", "DELL", "GOOG", "HPQ", "META", "MSFT"]


@app.on_event("startup")
def on_startup():
    create_pg_db_and_tables()


@app.get("/stock/{stock_symbol}")
async def get_stock(stock_symbol: str, db: Session = Depends(get_db)):
    """
     [GET] /stock/{stock_symbol}: returns the stock data for the given
    symbol. The endpoint should return a JSON object that includes all the
    fields of the Stock model mentioned above. Refer to the sources section
    for instructions from where to populate the above-mentioned Stock
    fields.
    """
    stock_symbol = stock_symbol.upper()
    if stock_symbol not in SUPPORTED_SYMBOLS:
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={
                "message": (
                    "Due to limitations of this small test, we only support following symbols: "
                    + ", ".join(SUPPORTED_SYMBOLS)
                    + "."
                )
            },
        )

    redis = get_redis()
    redis_key = REDIS_CACHE_KEY.format(symbol=stock_symbol)

    # return from cache if it exists
    stock_json: bytes = redis.get(redis_key)
    if stock_json:
        logger.info("got_stock_from_cache", extra={"stock_symbol": stock_symbol})
        return Response(
            status_code=status.HTTP_200_OK,
            media_type="application/json",
            content=stock_json.decode(),
        )

    # or update and save to db and cache
    now = datetime.now()
    yesterday = (now - timedelta(days=1)).date()
    stocks_cache_expiration = int(os.environ["STOCK_CACHE_EXPIRATION"])
    mw_data = MwLxmlCli().parse_for_stock(stock_symbol)
    polygon_data = PolygonAPICli().get_daily_open_close_agg(stock_symbol, yesterday)

    # get or create stock model
    stock = db.exec(
        select(Stock).where(Stock.company_code == stock_symbol)
    ).one_or_none()
    if stock is None:
        # create, we might want to save here in high demand systems.
        stock = Stock(company_code=stock_symbol)
        logger.info("stock_created", extra={"stock_symbol": stock_symbol})

    # pair with got_stock_from_cache to make some graphs
    logger.info("got_stock_from_db", extra={"stock_symbol": stock_symbol})

    stock.company_name = mw_data["company_name"]
    stock.request_date = now
    stock.stock_values = {
        "open": float(polygon_data.open),
        "high": float(polygon_data.high),
        "low": float(polygon_data.low),
        "close": float(polygon_data.close),
    }
    stock.performance_data = {
        "five_days": float(mw_data["performance"]["5 Day"]),
        "one_month": float(mw_data["performance"]["1 Month"]),
        "three_months": float(mw_data["performance"]["3 Month"]),
        "year_to_date": float(mw_data["performance"]["YTD"]),
        "one_year": float(mw_data["performance"]["1 Year"]),
    }
    for item in mw_data["competitors"]:
        stock.competitors.append(
            {
                "name": item["Name"],
                "market_cap": {
                    # TODO: There is some ETL to be done here, in currency and multiplier.
                    #  Should we always get then in USD?
                    "currency": item["Market Cap"][0],
                    "value": item["Market Cap"][1:-1],
                    "multiplier": item["Market Cap"][-1],
                },
            }
        )

    # save to db
    db.add(stock)
    db.commit()
    # it's so weird that sqlmodel don't keep the object Stock :), and then I need to do a refresh.
    db.refresh(stock)

    # save to redis, must convert to json first due to nested dicts.
    stock_json = stock.model_dump_json(exclude=["id"])
    redis.set(redis_key, stock_json, stocks_cache_expiration)

    logger.info("stock_updated", extra={"stock_symbol": stock_symbol})

    # return the JSON.
    return Response(
        status_code=status.HTTP_200_OK,
        media_type="application/json",
        content=stock_json,
    )


@app.post("/stock/{stock_symbol}")
async def update_stock(
    stock_symbol: str,
    amount: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Update the stock entity with the purchased amount based on received argument."""

    redis = get_redis()
    stock_symbol = stock_symbol.upper()
    amount = Decimal(amount)

    # get stock model, if it is already saved
    stock = db.exec(
        select(Stock).where(Stock.company_code == stock_symbol)
    ).one_or_none()

    if stock is None:
        # create
        stock = Stock(company_code=stock_symbol, purchased_amount=amount)
        logger.info("stock_created", extra={"stock_symbol": stock_symbol})
    else:
        # or update
        stock.purchased_amount += amount
        logger.info("got_stock_from_db", extra={"stock_symbol": stock_symbol})

    # save to db
    db.add(stock)
    db.commit()

    # expires cache
    redis.delete(REDIS_CACHE_KEY.format(symbol=stock_symbol))

    logger.info("stock_updated", extra={"stock_symbol": stock_symbol})

    # response
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": f"{amount} units of stock {stock_symbol} were added to your stock record"
        },
    )
