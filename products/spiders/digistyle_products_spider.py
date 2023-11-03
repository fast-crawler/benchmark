from bs4 import BeautifulSoup
from scrapy import Request
from scrapy import Spider
import json
import base64
from scrapy.item import Item, Field

from products.items import Product


class DigistyleProducts(Spider):

    name = 'digistyle-products'
    vendor_name = 'digistyle'
    start_urls=['https://www.digistyle.com']

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

    custom_settings = {
        'DOWNLOAD_TIMEOUT': 20,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 75,
        'RETRY_TIMES': 10,
        'DOWNLOADER_MIDDLEWARES_BASE': {
            'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
            # 'core.middlewares.proxy.ProxyMiddleware': 510,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 520,
            # 'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
            'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
            'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
        },
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.LifoMemoryQueue',
        # 'SPIDER_MIDDLEWARES': {
        #     'core.middlewares.spidermiddlewares.NotJsonMiddleware': 1
        # }
        }


    def get_category_request(self, category):
        return Request(
            url=f'https://www.digistyle.com/ajax{category}?pageno=1',
            callback=self.product_processor
            )

    def get_next_page_url(self, current_page):
        page_number = current_page.split('=')[-1]
        return current_page.replace(page_number, str(int(page_number) + 1))


    def parse(self, response, **kwargs):
        categories = response.css('a.c-mega-menu__link.c-mega-menu__link.js-mega-menu-ga-trigger::attr(href)').getall()
        for category in categories:
            # print(category)
            yield self.get_category_request(category)


    def product_processor(self, response, **kwargs):
        if response.status == 200:
            products = json.loads(response.body)['data']['click_impression']
            for product in products:
                item = Product()
                item.id = str(product['id'])
                item.vendor_name = self.vendor_name
                item.title = product['name']
                item.discounted_price = int(product['price_detail']['selling_price'])
                discount_percent = int(product['price_detail']['discount_percent'])
                item.base_price = int((item.discounted_price * 100)/(100-discount_percent))
                item.count = 1 if item.discounted_price else 0
                item.brand = product['brand']
                image_list = []
                image_list.append(product['image_src'])
                item.images = image_list
                item.category = str(product['site_category'][-1])
                item.url = self.generate_product_url(url=product['product_url'], product_id=item.id)
                print('this is the item', item)
                yield item

            if products:
                yield Request(
                    url=self.get_next_page_url(response.url),
                    callback=self.product_processor
                )

    def generate_product_url(self, url, product_id):
        def generate_affiliate_url(url):
            message_bytes = url.encode('utf-8')
            base64_bytes = base64.b64encode(message_bytes)
            base64_message = base64_bytes.decode('ascii')
            return f"https://migmig.affilio.ir/api/v1/Click/b/enoU4?b64={base64_message}"

        title = url.split("/")[-1]
        slug = product_id + "-" + title
        product_url = generate_affiliate_url(f'https://www.digistyle.com/product/{slug}')
        return product_url

