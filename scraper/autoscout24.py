# -*- coding: utf-8 -*-
import scrapy
import re
import datetime


def get_page_by_number(page_number):
    return f'https://www.autoscout24.it/lst?sort=standard&desc=0&fuel=B%2CC%2CL&ustate=N%2CU&lon=7.683066&lat=45.068375&zip=Torino&zipr=10&cy=I&priceto=5000&fregfrom=2010&atype=C&page={page_number}'

def clean_str(s):
    return " ".join(s).replace("\n", " ").strip()

def extract_dot_notation_int(s):
    s = clean_str(s)
    return int(float(re.findall("\d+\.*\d+", s)[0]) * 1000)

class Autoscout24Spider(scrapy.Spider):
    name = 'autoscout24'
    # allowed_domains = ['autoscout24.it/']
    start_urls = [get_page_by_number(1)]

    def __init__(self, *args, **kwargs):
        super(Autoscout24Spider, self).__init__(*args, **kwargs)
        self.page_index = 1
        self.max_page = 20



    def parse_vehicle(self, response):
        title = response.css(".cldt-detail-title")[0].css("*::text").extract()
        title = " ".join(title).replace("\n", " ").strip()

        price = response.css(".cldt-price")[0].css("*::text").extract()
        price = extract_dot_notation_int(price)

        key_facts = response.css(".cldt-stage-primary-keyfact")
        km = key_facts[0].css("*::text").extract()
        km = extract_dot_notation_int(km)

        matriculation = key_facts[1].css("*::text").extract()
        matriculation = clean_str(matriculation)
        matriculation = datetime.datetime.strptime(matriculation, '%m/%Y')

        env_section = response.xpath("//*[contains(text(),'Ambiente')]/following-sibling::div")
        fuel = clean_str(env_section.css("dd > a::text").extract())
        euroclass = clean_str(env_section.css("dd")[3].css("::text").extract())

        yield {
            "title": title,
            "price": price,
            "km": km,
            "matriculation": matriculation,
            "fuel": fuel,
            "euroclass": euroclass,
            "url": response.url
        }

    def parse(self, response):
        # yield scrapy.Request("https://www.autoscout24.it/annunci/fiat-punto-1-2-classic-5p-b-gpl-gpl-argento-d8b09aa3-ced1-47d3-aa3b-b89db8dc7584?cldtidx=1&cldtsrc=listPage", self.parse_vehicle)
        # return

        detail_links = response.css(
            'a[data-item-name="detail-page-link"]::attr(href)')

        for detail_link in detail_links.extract():
            print("\n\n\nparsing {detail_link}\n\n\n")
            yield scrapy.Request("https://autoscout24.it/" + detail_link, self.parse_vehicle)

        if self.page_index < self.max_page:
            self.page_index += 1
            yield scrapy.Request(get_page_by_number(self.page_index), self.parse)


