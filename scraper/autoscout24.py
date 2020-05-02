# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import datetime


def get_search_page(min_price, max_price,
                    page_number):
    return f'https://www.autoscout24.it/lst?sort=standard&size=20&desc=0&fuel=B%2CC%2CL&ustate=N%2CU&lon=7.683066&lat=45.068375&zip=Torino&offer=U&zipr=10&cy=I&pricefrom={min_price}&priceto={max_price}&kmfrom=10000&atype=C&page={page_number}'


def clean_str(s):
    if type(s) is list:
        s = " ".join(s)
    return s.replace("\n", "").strip()


def extract_dot_notation_int(s):
    s = clean_str(s)
    return int(float(re.findall("\d+\.*\d+", s)[0]) * 1000)

def get_int(s):
    s = clean_str(s)
    return int(re.findall("\d+", s)[0])

min_price = 2000
price_increment = 1000
max_price = 3000


class Autoscout24Spider(scrapy.Spider):
    name = 'autoscout24'
    # allowed_domains = ['autoscout24.it/']
    start_urls = [get_search_page(min_price=min_price,
                                  max_price=min_price+price_increment, 
                                  page_number=1)]

    def __init__(self, *args, **kwargs):
        super(Autoscout24Spider, self).__init__(*args, **kwargs)
        self.cur_page_index = 1
        self.max_page = 1
        self.cur_min_price = min_price

    def parse_vehicle(self, response):
        uuid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        car_uuid = re.findall(uuid_regex, response.url)[0]

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

        env_section = response.xpath(
            "//*[contains(text(),'Ambiente')]/following-sibling::div")
        fuel = clean_str(env_section.css("dd > a::text").extract())

        euroclass = ""

        try:
            euroclass = env_section.xpath(
                '//*[contains(text(), "Classe emissioni")]/following-sibling::dd').css("::text")[0]
            euroclass = euroclass.extract().replace("\n", "")
        except Exception as e:
            logging.error("Invalid euroclass")
            pass

        brand = clean_str( response.xpath('//*[contains(text(), "Caratteristiche")]/../*')[1].xpath("dd")[0].xpath("*/text()").extract()  )
        #brand = clean_str(response.xpath('//*[contains(text(), "Marca")]/following-sibling::dd/*/text()')[0].extract())
        model = None
        try:
            model = clean_str(response.xpath('//*[contains(text(), "Modello")]/following-sibling::dd/*/text()')[0].extract())
        except Exception as e:
            logging.error("Invalid model")
            pass

        doors = None
        try:
            doors = clean_str(response.xpath('//*[contains(text(), "Porte")]/following-sibling::dd/text()')[0].extract())
        except Exception as e:
            logging.warning("Invalid doors")
        engine_displacement = None
        try:
            engine_displacement = extract_dot_notation_int( response.xpath('//*[contains(text(), "Cilindrata")]/following-sibling::dd/text()')[0].extract() )
        except Exception as e:
            logging.warning("Invalid engine displacement")

        hp =  get_int(response.css(".cldt-stage-primary-keyfact").css(".sc-font-m ::text")[0].extract() )

        yield {
            "title": title,
            "price": price,
            "km": km,
            "matriculation": matriculation,
            "fuel": fuel,
            "euroclass": euroclass,
            "brand": brand,
            "model": model,
            "url": response.url,
            "doors": doors,
            "engine_displacement": engine_displacement,
            "hp": hp,
            "uuid": car_uuid
        }


    def parse(self, response):

        detail_links = response.css(
            'a[data-item-name="detail-page-link"]::attr(href)')
        for detail_link in detail_links.extract():
           logging.debug(f"\nparsing {detail_link}\n")
           yield scrapy.Request("https://autoscout24.it/" + detail_link, self.parse_vehicle)

        if self.cur_min_price + price_increment > max_price:
            print("\n\nFINISHED\n\n")
            return

        self.cur_page_index += 1

        if self.cur_page_index > self.max_page:
            self.cur_min_price = self.cur_min_price + price_increment
            print(f"Searching from {self.cur_min_price}...")
            self.cur_page_index = 1

        logging.debug(f"\n\n\npage={self.cur_page_index}\n\n\n\n")
        next_page_url = get_search_page(
            min_price=self.cur_min_price,
            max_price=self.cur_min_price+price_increment,
            page_number=self.cur_page_index)

        yield scrapy.Request(next_page_url, self.parse)
