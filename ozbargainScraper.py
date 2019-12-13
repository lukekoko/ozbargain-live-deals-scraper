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
from twilio.rest import Client
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


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
			logger.debug('Connecting to database')
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
		logger.debug('Database connected')

	def __enter__(self):
		return self

	def close(self):
		logger.debug("Closing database connection")
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
		# request data from ozbargin
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
			return dict
			self.searchDeals(dict)
			self.db.insertIntoSQL(dict)

	def searchDeals(self, dict):
		for term in self.searchTerms:
			if (re.search(r'(?i)' + re.escape(term), dict['title'])):
				Notifications().smsNotification(dict)
				return dict

class Notifications:
	def __init__(self):
		logger.debug('Notifications starting')
		self.smsMessage = '\nAn item from you list was posted. \n\nTimestamp: {} \nTitle: {} \nPrice: {} \nLink: {}'
		self.smsclient = Client(config.account_sid, config.auth_token)
		self.service = self.connectGmail()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		logger.debug('Notification done')

	def connectGmail(self):
		creds = None
		if os.path.exists('token.pickle'):
			with open('token.pickle', 'rb') as token:
				creds = pickle.load(token)
		# If there are no (valid) credentials available, let the user log in.
		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
					'credentials.json', SCOPES)
				creds = flow.run_local_server(port=0)
			# Save the credentials for the next run
			with open('token.pickle', 'wb') as token:
				pickle.dump(creds, token)
		service = build('gmail', 'v1', credentials=creds)
		return service

	def sendEmail():
		

	def smsNotification(self, dict):
		logger.info('Match found: %s', dict['title'])
		logger.debug('Sending sms') 
		message = smsclient.messages.create(
			body = self.smsMessage.format(dict['timestamp'], dict['title'], dict['price'], dict['link']),
			from_='+14843010951',
			to='+61478790532'
		)
		logger.debug('sms sent')

def main():
	# with Scraper() as live:
	# 	rawData = live.fetchData(1, 0)
	# 	extractedData = live.extractData(rawData)
	Notifications.connectGmail()



if __name__ == "__main__":
	setup()
	main()
