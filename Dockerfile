FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "./ozbargain-scraper/main.py"]

# sudo docker build -t "name" .
# sudo docker run -it --rm --name pythonrun "name"