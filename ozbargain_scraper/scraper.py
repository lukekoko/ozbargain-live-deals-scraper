from config import searchterms, config
from notifications import Notifications
from sql import SQL
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone, timedelta
import logging, logging.config, logging.handlers
import re
import time
import sys


currencyRegex = r"\$((?:[0-9]{1,3},(?:[0-9]{3},)*[0-9]{3}|[0-9]+)(?:\.[0-9][0-9])?)"
percentRegex = r"\d{1,2}%"

logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self):
        logger.debug("Scraper starting")
        self.liveurl = "https://www.ozbargain.com.au/api/live?last={}&disable=comments%2Cvotes%2Cwiki&types=Comp%2CForum"
        self.searchTerms = searchterms.searchTerms

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.debug("Scraper done")

    def fetchData(self, hours, mins):
        # request data from ozbargain
        timeInSec = int(
            (datetime.now() - timedelta(hours=hours, minutes=mins)).timestamp()
        )
        try:
            logger.info("Fetching data")
            request = requests.get(self.liveurl.format(timeInSec))
            liveDealsPage = json.loads(request.text)
            return liveDealsPage
        except TypeError:
            logger.error("Request to data failed", exc_info=True)
            raise TypeError

    def extractData(self, data):
        # extract title, price/percentage, link and timestamp
        logger.info("Extracting data from request")
        deals = []
        for i in data["records"]:
            dict = {}
            price = re.search(currencyRegex, i["title"])
            percentage = re.search(percentRegex, i["title"])
            dict["title"] = i["title"].replace('"', "")
            dict["link"] = "https://www.ozbargain.com.au" + i["link"]
            dict["price"] = (
                price.group() if price else percentage.group() if percentage else ""
            )
            dict["timestamp"] = datetime.fromtimestamp(i["timestamp"])
            deals.append(dict)
        logger.debug("Data extracted")
        return deals

    def searchDeals(self, deals):
        for deal in deals:
            term = self.searchDeal(deal)
            if term:
                yield term, deal

    def searchDeal(self, deal):
        for term in self.searchTerms:
            if re.search(r"(?i)" + re.escape(term), deal["title"]):
                return term
        return None

