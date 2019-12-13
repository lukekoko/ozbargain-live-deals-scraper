import config
import requests
from bs4 import BeautifulSoup
import json
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import pandas as pd
import re
import mysql.connector
import time
import sys

logger = logging.getLogger(__name__)

currencyRegex = r'\$((?:[0-9]{1,3},(?:[0-9]{3},)*[0-9]{3}|[0-9]+)(?:\.[0-9][0-9])?)'
percentRegex = r'\d{1,2}%'

def setup():
	# setting up logger
	logger.setLevel(config.settings['loggingLevel'])

	ch = logging.StreamHandler()
	ch.setLevel(config.settings['loggingLevel'])

	fh = TimedRotatingFileHandler(
		config.settings['logLoc'] + '/.log', when='midnight', interval=1
	)
	fh.suffix = "%Y%m%d"
	fh.setLevel(config.settings['loggingLevel'])

	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)
	fh.setFormatter(formatter)

	logger.addHandler(ch)
	logger.addHandler(fh)

class SQL:
	def __init__(self):
		try:
			logger.info('Connecting to database')
			self.db = mysql.connector.connect(
				host="localhost",
				port="3306",
				user="root",
				passwd="1234",
				database="ozbargin"
			)
		except mysql.connector.ProgrammingError:
			logger.error("Could not connect to database", exc_info=True)
			sys.exit(0)
		self.cur = self.db.cursor()
		self.insertQuery = 'INSERT INTO livedeals (timestamp, title, price, link) VALUES ("{0}", "{1}", "{2}", "{3}") ON DUPLICATE KEY UPDATE title="{1}", price="{2}", link="{3}"'

	def __enter__(self):
		return self

	def close(self):
		logger.info("Closing database connection")
		self.db.commit()
		self.cur.close()
		self.db.close()

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def insertIntoSQL(self, dict):
		try:
			query = self.insertQuery.format(
				dict['timestamp'], dict['title'], dict['price'], dict['link'])
			self.cur.execute(query)
		except mysql.connector.errors.IntegrityError:
			pass


class Scraper:
	def __init__(self, searchTerms):
		logger.debug('Scraper starting')
		self.dealsUrl = 'https://www.ozbargain.com.au/deals'
		self.liveurl = 'https://www.ozbargain.com.au/api/live?last={}&disable=comments%2Cvotes%2Cwiki&types=Comp%2CForum'
		self.searchTerms = searchTerms
		self.db = SQL()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		logger.debug('Scraper done')
		self.db.close()

	def fetchLiveDeals(self, hours, mins):
		# request data from ozbargin
		timeInSec = int((datetime.datetime.now() -
						 datetime.timedelta(hours=hours, minutes=mins)).timestamp())
		try:
			logger.debug('Fetching data')
			request = requests.get(self.liveurl.format(timeInSec))
			liveDealsPage = json.loads(request.text)
		except TypeError:
			logger.error("Request to data failed", exc_info=True)


		# extract title, price/percentage, link and timestamp
		for i in liveDealsPage['records']:
			dict = {}
			price = re.search(currencyRegex, i['title'])
			percentage = re.search(percentRegex, i['title'])
			dict['title'] = i['title'].replace('"', '')
			dict['link'] = 'https://www.ozbargain.com.au' + i['link']
			dict['price'] = price.group(
			) if price else percentage.group() if percentage else ''
			dict['timestamp'] = datetime.datetime.fromtimestamp(
				i['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
			self.searchDeals(dict)
			self.db.insertIntoSQL(dict)

	def searchDeals(self, dict):
		for term in self.searchTerms:
			if (re.search(r'(?i) \b' + re.escape(term) + r'\b', dict['title'])):
				logger.debug('Match found %s, %s', term, dict['title'])
				self.notification(dict)
				return dict

	def notification(self, dict):
		print(dict)





def main():
	searchTerms = ['nike', 'sandisk']
	with Scraper(searchTerms) as live:
		live.fetchLiveDeals(1, 0)


if __name__ == "__main__":
	setup()
	main()
