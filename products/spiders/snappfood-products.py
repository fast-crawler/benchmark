import json
from scrapy.http.request import Request
from products.items import Product, Store
from products.spiders import Spider


class SnappfoodProducts(Spider):
    name = 'snappfood-products'

    # vendor name is required to get backpack
    vendor_name = 'snappfood'

    backpack_settings = {
        'src': [
            'database:#metadata/snappfood/stores'
        ]
    }
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES_BASE': {
            'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
            # 'core.middlewares.proxy.ProxyMiddleware': 510,
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
                f'https://newapi.zoodfood.com/mobile/v2/restaurant/zooket-details?vendorCode={store["vendorCode"]}',
                self.parse_store,
                cb_kwargs={'store': store}
            )
            yield start_request

    def parse_store(self, response, store):
        response_json = json.loads(response.body)
        if response_json.get('status', False):
            if len(response_json["data"]["sections"]) == 0:
                return
            category_ids = (section['id'] for section in response_json["data"]["sections"])
            for category_id in category_ids:
                yield Request(
                    f'https://newapi.zoodfood.com/mobile/v2/product-variation/index?vendorCode={store["vendorCode"]}&menu_category_id={category_id}&page=0',
                    self.parse_products,
                    cb_kwargs={'store': store, 'category_id': category_id}
                )

    def parse_products(self, response, store, category_id):
        response_json = json.loads(response.body)
        if response_json.get('status', False):
            products = response_json["data"]["product_variations"]
            for product in products:
                images = []
                for image in product["images"]:
                    images.append(image["imageSrc"])
                p = Product()
                p.id = str(product["id"])
                p.title = product["title"]
                p.base_price = product["price"] * 10
                p.discounted_price = None
                p.description = product.get("description", None)
                p.category = response_json["data"]["meta"]["categoryTitle"]
                p.brand = product["brandTitle"]
                p.count = 0 if product["disabledUntil"] else 1
                p.images = images
                p.url = f'https://snappfood.ir/restaurant/menu/{store["vendorCode"]}'
                p.store = Store(store["vendorCode"], store["title"], store["address"])
                p.others = {
                    "score": product["score"],
                    "barcode": product["barcode"],
                    "rating": product["rating"]
                }
                yield p

            paging = response_json["data"]["meta"]["pagination"]
            if (paging["page"] + 1) * paging["size"] < paging["total"]:
                yield Request(
                    f'https://newapi.zoodfood.com/mobile/v2/product-variation/index?vendorCode={store["vendorCode"]}&menu_category_id={category_id}&page={paging["page"] + 1}',
                    self.parse_products,
                    cb_kwargs={'store': store, 'category_id': category_id}
                )
