from config import config
import logging
from scraper import Scraper
from notifications import Notifications
from sql import SQL
import time
import sys
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--hour', type=int, default=0,  help='How often to check for new deals (hour)')
parser.add_argument('--minute', type=int, default=5,  help='How often to check for new deals (minute)')
parser.add_argument('--noemail', default=True, action='store_false',  help='Disable email notification')
parser.add_argument('--nosms', default=True,  action='store_false', help='Disable sms notification')
parser.add_argument('--nosql', default=True, action='store_false', help='Disable storing deals in sql')
parser.add_argument('--nofb', default=True, action='store_false', help='Disable fb notification')

args = parser.parse_args()

logging.config.fileConfig(config.settings['logger_config'], disable_existing_loggers=False)
logger = logging.getLogger(__name__)

def scrape():
	with Scraper() as scrape:
		sender = None
		rawData = scrape.fetchData(args.hour, args.minute)
		extractedData = scrape.extractData(rawData)
		if (args.nosql):
			with SQL() as sql:
				sql.insertIntoSQL(extractedData)
		for deal in scrape.searchDeals(extractedData):
			logger.info('Deal found: %s', deal[1]['title'])
			if (sender == None):
				sender = Notifications()
			if (args.noemail):
				sender.sendEmail(deal)
			if (args.nosms):	
				sender.sendSMS(deal)
			if (args.nofb):
				sender.sendFB(deal)
			time.sleep(1)


def main():
	while True:
		try:
			scrape()
			wait = args.hour * 3600 + args.minute * 60
			logger.info('Waiting... for %ss', str(wait))
			time.sleep(wait)
		except KeyboardInterrupt:
			logging.info('Exiting...')
			sys.exit(0)

if __name__ == "__main__":
	main()