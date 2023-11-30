from scrapy import Request
from products.spiders import Spider
import json
from bs4 import BeautifulSoup
from datetime import date, timedelta


class MoponCoupon(Spider):
    name = 'mopon'
    
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
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

    start_urls = ['http://www.application.mopon.ir/api/coupon/get?category_id=JBGDg&order_by=newest&page=1']

    def get_coupon_details(self, coupon_id):
        return Request(
            url=f'http://www.application.mopon.ir/api/coupon/find/{coupon_id}',
            callback=self.coupon_details
        )

    def get_next_page_url(self, current_page):
        page_number = current_page.split('=')[-1]
        return current_page.replace(page_number, str(int(page_number) + 1))

    def parse(self, response, **kwargs):
        api_response = json.loads(response.body)['data']
        coupons = api_response['data']
        for coupon in coupons:
            yield self.get_coupon_details(coupon['id'])

        next_page = api_response['next_page_url']
        if next_page:
            yield Request(self.get_next_page_url(response.url))

    def coupon_details(self, response):
        coupon_details = json.loads(response.body)['data']
        # avoids sending coupons with null code
        if coupon_details['code']:
            vendor = coupon_details['name']
            expiration_date = str(coupon_details['expiration_date'])
            if expiration_date is None and coupon_details['is_expired'] == 0:
                # TODO: is_valid field should be added to the backend then every coupon spider will send is_valid for null coupons
                now = date.today()
                expiration_date = str(now + timedelta(days=2)) + "T00:00:00"

            if expiration_date:
                yield {
                    'source': self.name,
                    'title': coupon_details['title'].replace("\u200c", ""),
                    'description': coupon_details['content'].replace("\u200c", ""),
                    'vendor': vendor,
                    'expires_at': expiration_date,
                    'code': coupon_details['code'],
                }
