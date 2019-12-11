import requests
from bs4 import BeautifulSoup
import json
import datetime

timeSearch = int((datetime.datetime.now() - datetime.timedelta(minutes=30)).timestamp())
dealsUrl = 'https://www.ozbargain.com.au/deals'
liveurl = 'https://www.ozbargain.com.au/api/live?last={}&disable=comments%2Cvotes%2Cwiki&types=Comp%2CForum'.format(timeSearch) 

liveDealsPage = requests.get(liveurl)
liveData = json.loads(liveDealsPage.text)
for i in liveData['records']:
    print(i['title'])

newDealsPage = requests.get(dealsUrl)
soup = BeautifulSoup(newDealsPage.text, 'html.parser')
# for i in soup.find_all(class_='node-ozbdeal'):
#     print(i.h2.text)
#     print('https://ozbargain.com.au' + i.h2.a['href'])