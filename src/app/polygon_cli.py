import os
from datetime import date
from functools import cached_property

from polygon import RESTClient
from polygon.rest.models import DailyOpenCloseAgg


class PolygonAPICli:
    """Wraps polygon client."""

    @cached_property
    def client(self):
        # os.environ["POLYGON_API_KEY"] = "bmN7i7CrzrpKqFvgbB1fEaztCwZKSUjJ"
        try:
            # I like to have these kind of settings in Redis, so we can change then without restarting the processes
            # that is running. It's really useful to change to some fallback apis.
            api_key = os.environ["POLYGON_API_KEY"]
        except KeyError:
            raise ValueError(
                "You must configure POLYGON_API_KEY in docker-compose.yaml."
            )

        return RESTClient(api_key)

    def get_daily_open_close_agg(self, ticker: str, day: date) -> DailyOpenCloseAgg:
        """Get the open, close and afterhours prices of a stock symbol on a certain date."""
        print(day.isoformat())
        data = self.client.get_daily_open_close_agg(
            ticker, day.isoformat(), adjusted="true"
        )
        return data
