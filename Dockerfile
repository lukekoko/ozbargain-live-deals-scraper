FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR ozbargain_scraper

CMD ["python", "main.py", "--minute=1", "--nosms", "--noemail"]


