# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import datetime
import time


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
price_increment = 200
max_price = 14000


def get_title(response):
    title = response.css(".cldt-detail-title")[0].css("*::text").extract()
    title = " ".join(title).replace("\n", " ").strip()
    return title


def get_price(response):
    price = response.css(".cldt-price")[0].css("*::text").extract()
    price = extract_dot_notation_int(price)
    return price


def get_uuid(response):
    uuid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    car_uuid = re.findall(uuid_regex, response.url)[0]
    return car_uuid


def get_km_and_matriculation(response):
    key_facts = response.css(".cldt-stage-primary-keyfact")
    km = key_facts[0].css("*::text").extract()
    km = extract_dot_notation_int(km)

    matriculation = key_facts[1].css("*::text").extract()
    matriculation = clean_str(matriculation)
    matriculation = datetime.datetime.strptime(matriculation, '%m/%Y')
    return km, matriculation


def get_fuel_and_euroclass(response):
    env_section = response.xpath(
        "//*[contains(text(),'Ambiente')]/following-sibling::div")
    fuel = clean_str(env_section.css("dd > a::text").extract())

    euroclass = ""
    try:
        euroclass = env_section.xpath(
            '//*[contains(text(), "Classe emissioni")]/following-sibling::dd').css("::text")[0]
        euroclass = euroclass.extract().replace("\n", "")
    except Exception as e:
        logging.warning("Invalid euroclass")
        pass
    return fuel, euroclass


def get_brand(response):
    brand = response.xpath('//*[contains(text(), "Caratteristiche")]/../*')[
        1].xpath("dd")[0].xpath("*/text()").extract()
    brand = clean_str(brand)
    return brand


def get_model(response):
    model = None
    try:
        model = get_dd_item(response, "Modello")
    except Exception:
        logging.warning("Invalid model")
        pass
    return model


def get_dd_item(response, item_name):
    xpath_query = f'//*[contains(text(), "{item_name}")]/following-sibling::dd/text()'
    item = response.xpath(xpath_query)[0].extract()
    item = clean_str(item)
    return item


def get_doors(response):
    doors = None
    try:
        doors = get_dd_item(response, "Porte")
    except Exception as e:
        print(e)
        logging.warning("Invalid doors")
    return doors


def get_engine_displacement(response):
    engine_displacement = None
    try:
        engine_displacement = get_dd_item(response, "Cilindrata")
        engine_displacement = extract_dot_notation_int(engine_displacement)
    except Exception:
        logging.warning("Invalid engine displacement")
    return engine_displacement


def get_hp(response):
    hp = get_int(response.css(
        ".cldt-stage-primary-keyfact").css(".sc-font-m ::text")[0].extract())
    return hp


class Autoscout24Spider(scrapy.Spider):
    name = 'autoscout24'
    # allowed_domains = ['autoscout24.it/']
    start_urls = [get_search_page(min_price=min_price,
                                  max_price=min_price+price_increment,
                                  page_number=1)]

    def __init__(self, *args, **kwargs):
        super(Autoscout24Spider, self).__init__(*args, **kwargs)
        self.cur_page_index = 1
        self.max_page = 20
        self.cur_min_price = min_price

    def parse_vehicle(self, response):
        km, matriculation = get_km_and_matriculation(response)
        fuel, euroclass = get_fuel_and_euroclass(response)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                  time.gmtime(time.time()))

        yield {
            "title": get_title(response),
            "price": get_price(response),
            "km": km,
            "matriculation": matriculation,
            "fuel": fuel,
            "euroclass": euroclass,
            "brand": get_brand(response),
            "model": get_model(response),
            "doors": get_doors(response),
            "engine_displacement": get_engine_displacement(response),
            "hp": get_hp(response),
            "uuid": get_uuid(response),
            "url": response.url,
            "timestamp": timestamp,
        }

    def parse(self, response):
        logging.info(f"Processing {response.url}")
        detail_links = response.css(
            'a[data-item-name="detail-page-link"]::attr(href)')
        for detail_link in detail_links.extract():
            yield scrapy.Request("https://autoscout24.it/" + detail_link, self.parse_vehicle)

        if self.cur_min_price + price_increment > max_price:
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
