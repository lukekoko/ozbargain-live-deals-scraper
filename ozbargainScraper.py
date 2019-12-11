import requests
from bs4 import BeautifulSoup
import json
import datetime
import logging
import pandas as pd
import re
import mysql.connector

db = mysql.connector.connect(
  host="localhost",
  user="lkokoftopoulos",
  passwd="1234",
  database='ozbargain'
)

cur = db.cursor()

insert = 'INSERT INTO livedeals (timestamp, title, price, link) VALUES (%s, %s, %s, %s)'


currencyRegex = r'\$((?:[0-9]{1,3},(?:[0-9]{3},)*[0-9]{3}|[0-9]+)(?:\.[0-9][0-9])?)'
class Scraper:
	def __init__(self):
		self.dealsUrl = 'https://www.ozbargain.com.au/deals'
		self.liveurl = 'https://www.ozbargain.com.au/api/live?last={}&disable=comments%2Cvotes%2Cwiki&types=Comp%2CForum'
		try:
			self.df = pd.read_pickle('./store.pkl')
		except FileNotFoundError:
			self.df = pd.DataFrame(columns=['timestamp', 'title', 'price', 'link'])

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.df.to_pickle('./store.pkl')
		db.commit()

	def fetchLiveDeals(self, hours, mins):
		timeInSec = int((datetime.datetime.now() -
						  datetime.timedelta(hours=hours, minutes=mins)).timestamp())
		liveDealsPage = json.loads(requests.get(self.liveurl.format(timeInSec)).text)
		dict = {}
		for i in liveDealsPage['records']:
			price = re.findall(currencyRegex, i['title'])
			dict['title'] = i['title']
			dict['link'] = 'https://www.ozbargain.com.au' + i['link']
			dict['price'] = price[0] if len(price) > 0 else ''
			dict['timestamp'] = datetime.datetime.fromtimestamp(i['timestamp']).strftime('%d/%m/%y %H:%M:%S')
			try:
				cur.execute(insert, (dict['timestamp'], dict['title'], dict['price'], dict['link']))
			except mysql.connector.errors.IntegrityError:
				pass
			self.df = self.df.append(dict, ignore_index=True)
		print(self.df)

	def fetchNewDeals(self):
		newDealsPage = requests.get(self.dealsUrl)
		soup = BeautifulSoup(newDealsPage.text, 'html.parser')
		for i in soup.find_all(class_='node-ozbdeal'):
			print(i.h2.text)
			print('https://ozbargain.com.au' + i.h2.a['href'])
	
	def resetDF(self):
		self.df = self.df.iloc[0:0]


def main():
	with Scraper() as live:
		live.resetDF()
		live.fetchLiveDeals(24, 0)


if __name__ == "__main__":
	main()
