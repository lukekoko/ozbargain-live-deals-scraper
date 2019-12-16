#!/bin/bash
sudo docker stop ozbargain_scraper

sudo docker rm ozbargain_scraper

sudo docker build -t ozbargain_scraper .

sudo docker run \
--name ozbargain_scraper \
--mount type=bind,source=/home/luke/projects/ozbargain-scraper/logs/,target=/usr/src/app/logs/ \
--restart=always \
ozbargain_scraper