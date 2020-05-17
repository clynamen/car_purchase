FROM ubuntu:18.04
#COPY . /app
#RUN make /app
#CMD python /app/app.py

RUN apt-get update && apt-get install -y python3-pip wait-for-it
RUN python3 -m pip install scrapy influxdb pandas numpy
COPY scraper /scraper
#RUN cd /scraper/ &&  \
#    rm -f autoscout.csv && \
#    scrapy runspider autoscout24.py -s CLOSESPIDER_PAGECOUNT=1 -o autoscout.csv
