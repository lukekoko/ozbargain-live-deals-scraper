from scraper import Scraper
from notifications import Notifications

def main():
	with Scraper() as scrape:
		nots = Notifications()
		rawData = scrape.fetchData(1, 0)
		extractedData = scrape.extractData(rawData)
		for i in scrape.searchDeals(extractedData):
			nots.sendSMS(i)


if __name__ == "__main__":
	main()