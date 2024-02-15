import json
from scrapy.http import Response, Request
from products.spiders import Spider
from products.items import Product, Store
# from django.conf import settings as django_settings
import re


class SnappExpressProduct(Spider):
    name = 'snappexpress-products'
    vendor_name = 'snappexpress'
    start_urls = ['https://api.snapp.express/landing-rows/1?parse=1&variable=1']
    # backpack_settings = {
    #     'src': [f'database:#metadata/locations/{city}' for city in django_settings.LOCATIONS]
    # }

    custom_settings = {
        'DOWNLOAD_TIMEOUT': 20,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 75,
        'RETRY_TIMES': 10,
        'DOWNLOADER_MIDDLEWARES_BASE': {
            'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
            'core.middlewares.proxy.ProxyMiddleware': 510,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 520,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
            'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
            'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
        },
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.LifoMemoryQueue'
    }

    def next_page_url(self, url):
        page_index = re.search('&page=(.+?)', url).group(1)
        next_page = 'page=' + str(int(page_index) + 1)
        return url.replace(f'page={page_index}', next_page)

    def parse(self, response, **kwargs):
        categories = json.loads(response.body)['items']
        backpack_contents = self.backpack
        cities = []
        for city_name, city in backpack_contents.items():
            if isinstance(city, list) and city_name != 'stores':
                cities.append(city)
        for city in cities:
            for location in city:
                for category in categories:
                    if 'address_short' in location:
                        address = location['address_short']
                    else:
                        address = ''
                    yield Request(
                        url='https://api.snapp.express/mobile/v1/product/product-list?lat=%s&long=%s&filters=[]&extra-filter={"0":"{","1":"}","product_list_id":%s}&new_search=1&page_size=10&size=10&page=0' % (
                            location["lat"],
                            location["lon"],
                            category["data"]["linkId"]),
                        callback=self.parse_products,
                        cb_kwargs={
                            'address': address,
                            'lat': location['lat'],
                            'lon': location['lon']
                        }
                    )

    def parse_products(self, response, **location):
        page = json.loads(response.body)
        page_data = page["data"]
        if page["status"]:
            products = page_data["finalResult"]
            for product in products:
                item = Product()
                item.id = str(product['id'])
                product_data = product["data"]
                product_vendor = product_data["vendor"]
                item.vendor_name = self.vendor_name
                item.title = product_data['title']
                if 'price' in product_data:
                    item.base_price = product_data['price'] * 10
                    item.discounted_price = (product_data['price'] - product_data['discount']) * 10
                else:
                    item.base_price = None

                item.count = 0 if product_data["no_stock"] else 1
                item.url = self.generate_url(product_data)
                item.brand = product_data["brand"]
                item.category = page_data["title"]
                item.images = [img["main"] for img in product_data['images']]
                store_id = str(product_vendor["id"])
                if "address" in location:
                    store_address = f'{location["address"]}, {product_vendor["address"]}'
                else:
                    store_address = f'{product_vendor["address"]}'
                lat = str(product_vendor['latitude'])
                lon = str(product_vendor['longitude'])
                item.store = Store(store_id, product_vendor["title"], store_address, lat, lon)
                yield item
            if products:
                yield Request(
                    url=self.next_page_url(url=response.url),
                    callback=self.parse_products,
                    cb_kwargs=location
                )

    def generate_url(self, product_data):
        vendor = product_data["vendor"]
        vendor_slug = self.slugify(vendor['title'])
        title_slug = self.slugify(product_data['title'])
        vendor_code = vendor["vendorCode"]
        return f'https://m.snapp.express/supermarket/{vendor_slug}-z-{vendor_code}/product/{title_slug}-p{product_data["id"]}'

    def slugify(self, input_str):
        return input_str.replace(" ", "_").replace(")", "_").replace("(", "_")
