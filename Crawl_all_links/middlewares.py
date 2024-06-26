# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import re
from typing import Tuple, Optional, Dict

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

from Crawl_all_links import config
from Crawl_all_links.proxy.fast_proxy_tunnel import IpProxy_2
from Crawl_all_links.proxy.proxy_ip_pool import create_ip_pool
from Crawl_all_links.proxy.proxy_ip_provider import IpInfoModel
import random

from Crawl_all_links.tools import utils


class CrawlAllLinksSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class CrawlAllLinksDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    media_regex = re.compile(
        r'\.(mp4|jpg|png|gif|pdf|docx|xls|css|js|doc|word|xlsx|ppt|pptx|zip|rar|tar|tar.gz|taz|exe|apk|dmg|msi|app|json|mp3|wav|ogg|m4a|flac|avi|mov|wmv|flv|webm|xml|jpeg|bmp|tiff|tif|svg|webp)$',
        re.IGNORECASE)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        if self.media_regex.search(request.url):
            # 修改原始请求的方法为 HEAD，避免下载内容
            request.method = 'HEAD'


        if config.ENABLE_IP_PROXY:
            proxy_url_list = IpProxy_2.get_proxies(2)
            if proxy_url_list:  # 检查代理列表是否为空
                selected_proxy = random.choice(proxy_url_list)
                request.meta['proxy'] = selected_proxy['http']
                spider.logger.info(f"使用的代理ip为: {selected_proxy['http']}")
            else:
                utils.logger.warning("No proxy URLs available.")


        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
