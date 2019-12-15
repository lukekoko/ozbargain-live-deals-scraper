#!/bin/bash
sudo docker stop ozbargain-scraper

sudo docker rm ozbargain-scraper

sudo docker build -t ozbargain-scraper .

sudo docker run \
--name ozbargain-scraper \
--mount type=bind,source=/home/luke/projects/ozbargain-scraper/logs/,target=/usr/src/app/logs/ \
--restart=always \
ozbargain-scraper