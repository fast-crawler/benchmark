from scrapy import Request
from products.spiders import Spider
from datetime import date, timedelta


class OffchCoupon(Spider):
    name = 'offch'
    
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
    start_urls = ['https://api.offch.com/api/coupons?category=1&limit=10&format=json']

    def parse(self, response, **kwargs):
        response = response.json()
        
        if response['next'] is not None:
            yield Request(response['next'])

        for coupon in response['results']:
            if coupon['code'] is not None:
                expiration_date = coupon['expire_datetime']
                if expiration_date is None and coupon['is_expired'] is False:
                    # TODO: is_valid field should be added to the backend then every coupon spider will send is_valid for null coupons
                    now = date.today()
                    expiration_date = str(now + timedelta(days=2)) + "T00:00:00"
                if expiration_date:
                    yield {
                        'source': self.name,
                        'title': coupon['title'],
                        'description': coupon['description'],
                        'vendor': coupon['shop']['name'],
                        'expires_at': expiration_date,
                        'percentage': coupon['percent'],
                        'amount': coupon['value'],
                        'ceiling': coupon['max_value'],
                        'code': coupon['code'][0],
                        'min_order': coupon['min_order']
                    }
