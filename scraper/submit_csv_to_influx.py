#!/usr/bin/env python3
from influxdb import InfluxDBClient
import pandas as pd
import argparse
import sys


class InfluxSubmit:

    def __init__(self, csv_fname, db_addr, username, password):
        self.csv_fname = csv_fname
        self.db_addr = db_addr
        self.username = username
        self.password = password

        addr, port = db_addr.split(":")
        port = int(port)

        db_name = 'autoscout_turin'

        self.client = InfluxDBClient(host=addr, port=port)
        self.client.switch_database(db_name)

    def run(self):
        df = pd.read_csv(self.csv_fname)

        json_points = []

        for _, car in df.iterrows():
            car_json = {
                "measurement": "car",
                "tags": {
                    "car": car['title'],
                    "id": car['uuid'],
                    "url": car['url']
                },
                "time": car['timestamp'],
                "fields": {
                    "price": car['price'],
                    "km": car['km'],
                }
            }
            json_points.append(car_json)

        self.client.write_points(json_points)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    parser.add_argument("db_addr")
    parser.add_argument("-u", required=False)
    parser.add_argument("-p", required=False)

    args = parser.parse_args()

    submitter = InfluxSubmit(args.csv_file, args.db_addr,
                             args.u, args.p)
    submitter.run()
