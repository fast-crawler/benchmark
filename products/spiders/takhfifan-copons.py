from bs4 import BeautifulSoup
from scrapy import Request
from products.spiders import Spider


class TakhfifanCoupon(Spider):
    name = 'takhfifan'
    
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
    start_urls = ['https://takhfifan.com/v4/api/rainman/vendors?limit=1000']

    def parse(self, response):
        response = response.json()
        for vendor in response['data']:
            yield Request(
                f'https://takhfifan.com/v4/api/rainman/vendors/{vendor["attributes"]["slug"]}/offers?limit=1000&filter_by=coupon,cashpon',
                callback=self.parse_coupon)

    def parse_coupon(self, response):
        response = response.json()
        for offer in response['data']:
            yield Request(f'https://takhfifan.com/v4/api/rainman/offers/{offer["id"]}/coupons/invalidate',
                          callback=self.parse_coupon_detailed,
                          cb_kwargs={'offer': offer['attributes']})

    def parse_coupon_detailed(self, response, offer):
        response = response.json()
        if offer['expires_at']:
            yield {
                'source': self.name,
                'title': offer['title'],
                'description': BeautifulSoup(offer['description'], features='lxml').text,
                'vendor': offer['vendor']['name'],
                'expires_at': offer['expires_at'],
                'percentage': offer['percentage'],
                'amount': offer['amount'],
                'ceiling': offer['ceiling'],
                'code': response['data']['attributes']['code'],
            }
