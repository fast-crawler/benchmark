import json
import base64
from scrapy.http.request import Request
from products.items import Product, Store
from products.spiders import Spider


class DigikalajetProducts(Spider):
    name = 'digikalajet-products'

    # vendor name is required to get backpack
    vendor_name = 'digikalajet'

    backpack_settings = {
        'src': [
            'database:#metadata/digikalajet/stores'
        ]
    }

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
        }
    }

    def start_requests(self):
        stores = self.backpack['stores']
        for store in stores:
            start_request = Request(
                f'https://api.digikalajet.ir/shop/{store["id"]}/?latitude=35.69&longitude=51.33',
                cb_kwargs=store
            )
            yield start_request

    def get_category_products(self, category, store):
        return Request(
            url=f'https://api.digikalajet.ir/shop/{store["id"]}/{category["id"]}/products/?page=1&latitude=36.25&longitude=59.61',
            cb_kwargs={'category': category, 'store': store},
            callback=self.parse_category_products
        )

    def next_page_url(self, url, current_page):
        current = 'page=' + str(current_page)
        next_page = 'page=' + str(current_page + 1)
        return url.replace(current, next_page)

    def get_store_address(self, store_info, address_short, address):
        if len(store_info) == 2:
            store_address = address_short + store_info[1]
            return store_address
        else:
            return address

    def parse(self, response, **store):
        main_page = json.loads(response.body)
        if 'body' in main_page['data']:
            items = main_page['data']['body']['widgets']
            categories = None
            for item in items:
                if item['type'] == 'category_list':
                    categories = item['data']['categories']
            for category in categories:
                yield self.get_category_products(category=category, store=store)

    def parse_category_products(self, response, **additional_info):
        data = json.loads(response.body)['data']
        products = data['products']
        for product in products:
            item = Product()
            item.id = str(product['id'])
            item.vendor_name = self.vendor_name
            item.title = product['title']
            if 'price' in product:
                price_info = product['price']
                item.base_price = price_info['price']
                item.discounted_price = price_info['price'] - price_info['discount']
            else:
                item.base_price = None
                item.count = 0
            item.url = self.generate_affiliate_url(f'https://www.digikalajet.com/shop/product/{additional_info["store"]["id"]}/{product["id"]}')
            item.count = 1 if product['stock']['has_stock'] else 0
            item.category = additional_info["category"]["title"]
            images_list = []
            images_list.append(product["media"])
            item.images = images_list
            store_id = str(additional_info["store"]["id"])
            store_info = additional_info["store"]['title'].split('|')
            address_short = additional_info["store"]["location"]['address_short']
            address_long = additional_info["store"]["location"]['address']
            store_address = self.get_store_address(store_info=store_info, address_short=address_short, address=address_long)
            store_name = store_info[0].strip()
            lat = additional_info["store"]["location"]['lat']
            lon = additional_info["store"]["location"]['lon']
            item.store = Store(store_id, store_name, store_address, lat, lon)
            yield item
        current_page = data['pager']['current_page']
        total_pages = data['pager']['total_pages']
        if current_page < total_pages:
            yield Request(
                url=self.next_page_url(url=response.url, current_page=current_page),
                cb_kwargs=additional_info
            )

    def generate_affiliate_url(self, url):
        message_bytes = url.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        return f"https://migmig.affilio.ir/api/v1/Click/b/vsDFG?b64={base64_message}"

