import pytest

from app.marketwatch_cli import MwLxmlCli


@pytest.mark.parametrize(
    "stock", ["AAPL", "AMZN", "DELL", "GOOG", "HPQ", "META", "MSFT"]
)
def test_mw_cli(stock):
    """test general structure of MwLxmlCli."""
    cli = MwLxmlCli()
    data = cli.parse_for_stock(stock)
    # we may have no competitors, but if have we check the structure for each one.
    # I didn't want to test the values however because the test would be really long.
    for item in data["competitors"]:
        assert list(item.keys()) == ["Name", "Chg %", "Market Cap"]
        assert [type(v) for v in item.values()] == [str, str, str]
    assert list(data["performance"].keys()) == [
        "5 Day",
        "1 Month",
        "3 Month",
        "YTD",
        "1 Year",
    ]
    assert [type(v) for v in data["performance"].values()] == [str, str, str, str, str]
