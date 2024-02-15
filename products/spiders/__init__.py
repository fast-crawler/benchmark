# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
from scrapy import Spider as BaseSpider


class Spider(BaseSpider):
    backpack = None
    backpack_settings = None
    vendor_name = None

    def __init__(self, name=None, backpack=None, *args, **kwargs):
        super().__init__(name, **kwargs)
        self.backpack = backpack


class DefaultSpider(Spider):
    name = 'default'
    vendor_name = 'default_vendor'
