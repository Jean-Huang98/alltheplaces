# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
from urllib.parse import urlencode
import json


class SallySpider(scrapy.Spider):
    name = "sallybeauty"
    allowed_domains = ["sallybeauty.com"]

    def start_requests(self):
        base_url = "https://www.sallybeauty.com/on/demandware.store/Sites-SA-Site/default/Stores-FindStores?"

        params = {
            "showmap": "true",
            "radius": "100",
        }

        with open('./locations/searchable_points/us_centroids_100mile_radius.csv') as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(',')
                params.update({"lat": lat, "long": lon})
                yield scrapy.Request(url=base_url + urlencode(params))

    def parse_hours(self, hours):
        hrs = Selector(text=hours)
        days = hrs.xpath('//div[@class="store-hours-day"]/text()').extract()
        hours = hrs.xpath('//div[@class="store-hours-day"]/span/text()').extract()

        opening_hours = OpeningHours()

        for d, h in zip(days, hours):
            day = d.strip(': ')
            open_time, close_time = h.split(' - ')
            open_time = open_time.lstrip('0')
            opening_hours.add_range(day=day[:2],
                                    open_time=open_time,
                                    close_time=close_time,
                                    time_format="%I:%M %p")

        return opening_hours.as_opening_hours()

    def parse(self, response):
        jdata = json.loads(response.body_as_unicode())

        for row in jdata.get('stores',[]):

            properties = {
                'ref': row["ID"],
                'name': row["name"],
                'addr_full': " ".join([row["address1"], row.get("address2", "") or ""]).strip(),
                'city': row["city"],
                'postcode': row["postalCode"],
                'lat': row["latitude"],
                'lon': row["longitude"],
                'phone': row["phone"],
                'state': row["stateCode"],
            }

            yield GeojsonPointItem(**properties)
