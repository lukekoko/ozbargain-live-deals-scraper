from config import config
import requests
from bs4 import BeautifulSoup
import json
import datetime
import logging, logging.config, logging.handlers
import pandas as pd
import re
import time
import sys
from notifications import Notifications
from sql import SQL


currencyRegex = r'\$((?:[0-9]{1,3},(?:[0-9]{3},)*[0-9]{3}|[0-9]+)(?:\.[0-9][0-9])?)'
percentRegex = r'\d{1,2}%'

logging.config.fileConfig('./config/logger.ini')
logger = logging.getLogger(__name__)


class Scraper:
	def __init__(self):
		logger.debug('Scraper starting')
		self.dealsUrl = 'https://www.ozbargain.com.au/deals'
		self.liveurl = 'https://www.ozbargain.com.au/api/live?last={}&disable=comments%2Cvotes%2Cwiki&types=Comp%2CForum'
		self.searchTerms = config.searchTerms
		self.db = SQL()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		logger.debug('Scraper done')
		self.db.close()

	def fetchData(self, hours, mins):
		# request data from ozbargain
		timeInSec = int((datetime.datetime.now() -
						 datetime.timedelta(hours=hours, minutes=mins)).timestamp())
		try:
			logger.debug('Fetching data')
			request = requests.get(self.liveurl.format(timeInSec))
			liveDealsPage = json.loads(request.text)
			return liveDealsPage
		except TypeError:
			logger.error("Request to data failed", exc_info=True)
			raise TypeError

	def extractData(self, data):
		# extract title, price/percentage, link and timestamp
		deals = []
		for i in data['records']:
			dict = {}
			price = re.search(currencyRegex, i['title'])
			percentage = re.search(percentRegex, i['title'])
			dict['title'] = i['title'].replace('"', '')
			dict['link'] = 'https://www.ozbargain.com.au' + i['link']
			dict['price'] = price.group(
			) if price else percentage.group() if percentage else ''
			dict['timestamp'] = datetime.datetime.fromtimestamp(
				i['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
			deals.append(dict)
		return deals
			# self.searchDeals(dict)
			# self.db.insertIntoSQL(dict)
	def searchDeals(self, deals):
		for deal in deals:
			for term in self.searchDeal(deal):
				yield deal

	def searchDeal(self, deal):
		for term in self.searchTerms:
			if (re.search(r'(?i)' + re.escape(term), deal['title'])):
				yield term



