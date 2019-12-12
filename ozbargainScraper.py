import requests
from bs4 import BeautifulSoup
import json
import datetime
import logging
import pandas as pd
import re
import mysql.connector
import time
import sys

db = mysql.connector.connect(
  host="localhost",
  port="3306",
  user="root",
  passwd="1234",
  database="ozbargin"
)

cur = db.cursor()

insert = 'INSERT INTO livedeals (timestamp, title, price, link) VALUES ("{0}", "{1}", "{2}", "{3}") ON DUPLICATE KEY UPDATE title="{1}", price="{2}", link="{3}"'


currencyRegex = r'\$((?:[0-9]{1,3},(?:[0-9]{3},)*[0-9]{3}|[0-9]+)(?:\.[0-9][0-9])?)'
class Scraper:
	def __init__(self):
		self.dealsUrl = 'https://www.ozbargain.com.au/deals'
		self.liveurl = 'https://www.ozbargain.com.au/api/live?last={}&disable=comments%2Cvotes%2Cwiki&types=Comp%2CForum'
		# try:
		# 	self.df = pd.read_pickle('./store.pkl')
		# except FileNotFoundError:
		# 	self.df = pd.DataFrame(columns=['timestamp', 'title', 'price', 'link'])

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		# self.df.to_pickle('./store.pkl')
		db.commit()

	def fetchLiveDeals(self, hours, mins):
		print('Fetching deals')
		timeInSec = int((datetime.datetime.now() -
						  datetime.timedelta(hours=hours, minutes=mins)).timestamp())
		liveDealsPage = json.loads(requests.get(self.liveurl.format(timeInSec)).text)
		dict = {}
		for i in liveDealsPage['records']:
			price = re.findall(currencyRegex, i['title'])
			dict['title'] = i['title'].replace('"', '')
			dict['link'] = 'https://www.ozbargain.com.au' + i['link']
			dict['price'] = price[0] if len(price) > 0 else ''
			dict['timestamp'] = datetime.datetime.fromtimestamp(i['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
			try:
				query = insert.format(dict['timestamp'], dict['title'], dict['price'], dict['link'])
				cur.execute(query)
			except mysql.connector.errors.IntegrityError:
				pass
			# self.df = self.df.append(dict, ignore_index=True)
		# print(self.df)

	def fetchNewDeals(self):
		newDealsPage = requests.get(self.dealsUrl)
		soup = BeautifulSoup(newDealsPage.text, 'html.parser')
		for i in soup.find_all(class_='node-ozbdeal'):
			print(i.h2.text)
			print('https://ozbargain.com.au' + i.h2.a['href'])
	
	def resetDF(self):
		self.df = self.df.iloc[0:0]


def main():
	while True:
		try:
			with Scraper() as live:
				live.fetchLiveDeals(0, 6)
				# live.resetDF()
			print('waiting for %s' % '5mins')
			time.sleep(300)
		except KeyboardInterrupt:
			sys.exit(0)
		


if __name__ == "__main__":
	main()
