from typing import Dict, List

from lxml import html


class MwLxmlCli:
    """This class deals with MarketWatch scraping."""

    def load_stock(self, stock):
        """Load html source from fixture files."""

        # HEADS UP: outside of tests, we will face captchas and network errors. For this test, requesting marketwatch
        # required a catpcha solver, and while would be nice to solved that problem, it would require a third party
        # service.
        # In my vision, CIAL may have a microservice or lambda that download this html sources and cache it, eliminating
        # the need to solve the capcha.
        # Because of that complexity I choose to just save sources of some pages and load from disk.
        # The supported stocks are AAPL, AMZN, DELL, GOOG, HPQ, META, MSFT.

        with open(
            f"/src/tests/fixtures/mw_{stock}.html", "r", encoding="utf-8"
        ) as file:
            return file.read()

    def parse_for_stock(self, stock) -> Dict:
        # Load and parse the HTML file
        stock = stock.lower()
        html_content = self.load_stock(stock)
        tree = html.fromstring(html_content)
        data = dict()

        # setting each item in dict is better to debug
        data["competitors"] = self.load_competitors(tree)
        data["performance"] = self.load_peformance(tree)
        data.update(**self.load_company_name(tree))
        return data

    def load_competitors(self, tree) -> List[Dict]:
        """Given the HTML source, gets content from Competitors table."""
        tables = tree.xpath("//div[contains(@class, 'Competitors')]//table")
        if not tables:
            return []

        table_data = []
        table = tables[0]

        # Here we have a usual table with columns "Name", "Chg %" and "Market Cap"
        headers = [th.text_content().strip() for th in table.xpath(".//th")]
        for row in table.xpath(".//tr"):
            # Values in this table has some "\n    " strings. split() take care of extra \n and spaces.
            values = [" ".join(td.text_content().split()) for td in row.xpath(".//td")]
            if values:  # Ensure it's not an empty row
                table_data.append(dict(zip(headers, values)))  # Map headers to values

        return table_data

    def load_peformance(self, tree) -> Dict:
        """Given the HTML source, gets content from Performance table."""
        tables = tree.xpath(
            "//div[contains(@class, 'element--table') and contains(@class, 'performance')]//table"
        )
        if not tables:
            return {}

        table_data = {}
        table = tables[0]

        # Here we have headers as first td and value in second td for each row.
        for row in table.xpath(".//tr"):
            cell1, cell2, *_ = row.xpath(".//td")
            period = cell1.text_content().strip()
            # Extract values from <li class="content__item value">
            # Used join and split instead going deep in xpath because looks faster. Let the code example for reference.
            # value = cell2.xpath(".//li[contains(@class, 'content__item') and contains(@class, 'value')]")[0].text_content().strip()
            value = " ".join(cell2.text_content().split()).replace("%", "")
            table_data[period] = value

        return table_data

    def load_company_name(self, tree) -> Dict:
        name = (
            tree.xpath("//h1[contains(@class, 'company__name')]")[0]
            .text_content()
            .strip()
        )
        return {"company_name": name}
