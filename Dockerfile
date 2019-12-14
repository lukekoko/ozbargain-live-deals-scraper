FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "./ozbargain-scraper/main.py"]

# sudo docker build -t ozbargain-scraper .
# sudo docker run -v ~/projects/ozbargain-scraper/logs/:/usr/src/app/logs/ --name ozbargain-scraper ozbargain-scraper