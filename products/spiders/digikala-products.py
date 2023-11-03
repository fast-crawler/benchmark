import base64
from urllib import parse
from scrapy import Request
from products.items import Product
from products.spiders import Spider
import json


class DigikalaProducts(Spider):

    name = 'digikala-products'
    vendor_name = 'digikala'

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
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
            'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
            'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
        },
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.LifoMemoryQueue',
        'SPIDER_MIDDLEWARES': {
            # 'core.middlewares.spidermiddlewares.NotJsonMiddleware': 1
        }
    }

    def start_requests(self):
        # to get all subcategories of supermarket products
        # to get all subcategories of clothes
        category_ids = ['8749', '8895']
        for category_id in category_ids:
            yield Request(
                f'https://sirius.digikala.com/v1/categories/{category_id}/',
                meta={
                    'max_retry_times': 100
                }
            )

    def get_product_detail(self, product_id, category):
        return Request(
            url=f'https://sirius.digikala.com/v1/product/{product_id}/',
            callback=self.extract_product_details,
            cb_kwargs=category,
            meta={
                'max_retry_times': 100
            }
        )

    def get_category_products(self, page_number, super_category, category):
        # this is sent for each supermarket subcategory
        additional_info = {"page_number": page_number, "category": category, "super_category": super_category}
        return Request(
            # swap the api from web to android if something changes
            # copy https://sirius.digikala.com/v1/category/{category["id"]}/?sort=7&page={page_number} to url place
            # bellow to swap to android api keep in mind android api for category has 100 page limitation
            url=f'https://api.digikala.com/v1/categories/{category["code"]}/search/?page={page_number}',
            callback=self.category_details,
            meta={
                'max_retry_times': 100
            },
            cb_kwargs=additional_info
        )

    def parse(self, response, **kwargs):
        # getting the list of supermarket categories
        items = json.loads(response.body)['data']
        categories = list()
        for item in items:
            if item['type'] == "category_pane":
                categories = item['data']['categories']
        # the next five lines are for clothes category since it has slightly different api endpoint
        if not categories:
            for item in items:
                if item['type'] == "category_child_view":
                    for cat in item['data']['child']:
                        categories.append(cat)
        for category in categories:
            yield self.get_category_products(page_number=1, category=category, super_category=category)

    def category_details(self, response, **additional_info):
        category_details = json.loads(response.body)
        # this is the condition for stopping recursive calls when we hit an empty page for the category
        if 'data' in category_details:
            category_details = category_details['data']
            total_products = category_details['pager']['total_items']
            total_pages = category_details['pager']['total_pages']
            products_per_page = len(category_details['products'])
            subcategories = None
            # gets all sub categories of current category
            if 'sub_categories_best_selling' in category_details:
                subcategories = category_details['sub_categories_best_selling']
            # this is the condition to check if a category has less products than api limitation
            # currently api limitation is 100 pages per category and each page has 20 products
            # therefore total products should be less than 20*100
            # if total products are more than limitation we should crawl sub categories instead
            if total_products > 100 * products_per_page and subcategories:
                category = additional_info['category']
                super_category = additional_info['super_category']
                for subcategory in subcategories:
                    yield self.get_category_products(page_number=1, category=subcategory, super_category=super_category)
            # if total products are less than limitation we can crawl products in the same category
            else:
                products = category_details['products']
                for product in products:
                    # calls all the products available in the current category page
                    yield self.get_product_detail(product_id=product['id'], category=additional_info['super_category'])

                next_page = additional_info['page_number'] + 1
                category = additional_info['category']
                super_category = additional_info['super_category']
                # calls the next page of this category
                yield self.get_category_products(page_number=next_page, category=category, super_category=super_category)

    def extract_product_details(self, response, **category):
        response_body = json.loads(response.body)
        if 'data' in response_body:
            product_detail = response_body['data']['product']
            item = Product()
            item.id = str(product_detail['id'])
            item.vendor_name = self.vendor_name
            item.title = product_detail['title_fa']
            price_info = product_detail['price']
            # checks if product is in stock
            if len(price_info) != 0:
                # recommended retail price aka without discount
                item.base_price = int(price_info['rrp_price'])
                item.discounted_price = int(price_info['selling_price'])
                item.count = 1
            else:
                item.count = 0
                item.base_price = 0
                item.discounted_price = 0
            item.url = self.generate_affiliate_url(f'https://www.digikala.com/product/dkp-{product_detail["id"]}/')
            if "brand" in product_detail:
                item.brand = product_detail['brand']['title_fa']
            item.category = category['title_fa']
            images_list = []
            main_image = product_detail['images']['main']
            images_list.append(main_image)
            for image in product_detail['images']['image_list']:
                if image != main_image:
                    images_list.append(image)
            item.images = images_list
            if "description" in product_detail['review']:
                item.description = product_detail['review']['description']

            yield item

    def generate_affiliate_url(self, url):
        message_bytes = url.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        return f"https://migmig.affilio.ir/api/v1/Click/b/wMFf5?b64={base64_message}"
