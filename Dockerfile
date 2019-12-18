FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR ozbargain_scraper

CMD ["python", "main.py", "--hour=23", "--minute=60", "--nosms"]


