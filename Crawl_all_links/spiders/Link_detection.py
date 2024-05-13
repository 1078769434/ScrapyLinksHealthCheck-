from urllib.parse import urlparse
import scrapy
from Crawl_all_links.utils.log_config import logger
from Crawl_all_links.items import CrawlAllLinksItem
from Crawl_all_links.spiders.base_spider import BaseSpider

from scrapy.exceptions import NotSupported
from scrapy.spidermiddlewares.httperror import HttpError


class LinkDetectionSpider(BaseSpider):
    name = "Link_detection"

    def parse(self, response):

        # 从response.meta中获取当前深度
        depth = response.meta.get('depth', 0)
        logger.info(f"当前URL {response.url} 的爬取深度为: {depth}")
        # 定义一个包含可能包含链接的标签和属性的列表
        link_selectors = [
            ('//a/@href', 'a'),
            ('//img/@src', 'img'),
            ('//link/@href', 'link'),
            ('//script/@src', 'script'),
            ('//iframe/@src', 'iframe'),
            ('//source/@src', 'source'),
            ('//source/@srcset', 'source_set'),
            ('//embed/@src', 'embed'),
            ('//object/@data', 'object'),
            ('//video/@src', 'video'),
            ('//audio/@src', 'audio')
        ]

        # 遍历选择器，提取并转换链接
        for selector, _ in link_selectors:
            try:
                for link in response.xpath(selector).extract():
                    url = response.urljoin(link)
                    parsed_url_to_check = urlparse(url)
                    if parsed_url_to_check.netloc == self.domain and url not in self.visited_urls:
                        self.visited_urls.add(url)
                        yield scrapy.Request(url=url, callback=self.parse, errback=self.errback)
                        yield scrapy.Request(url, callback=self.parse_content, errback=self.errback)
                    elif not parsed_url_to_check.netloc == self.domain and url not in self.visited_urls:
                        self.visited_urls.add(url)
                        yield scrapy.Request(url=url, callback=self.parse_content, errback=self.errback,
                                         meta={'referer': response.url})  # 解析页面内容
            except NotSupported as e:
                logger.error(e)
                yield scrapy.Request(url=response.url, callback=self.parse_content, errback=self.errback,
                                     meta={'referer': response.url})  # 解析页面内容


    def parse_content(self, response):
        item = CrawlAllLinksItem()

        referer_header = response.request.headers.get('Referer')
        referer = self.process_referer(referer_header)
        item['url'] = response.url
        item['status_code'] = response.status
        item['category'] = self.check_url_category(response.url)
        item['is_external'] = self.is_external_link(response.url)
        item['etag'] = self.extract_header(response, 'etag')
        item['last_modified'] = self.parse_datetime_header(
            response.headers.get('Last-Modified') or response.headers.get('last-modified') or response.headers.get(
                'LAST-MODIFIED'))
        item['referer'] = referer
        yield item

    def errback(self, failure):

        self.logger.error(f'Request failed: {failure.request.url}, Reason: {failure.value.response.status}')

        item = CrawlAllLinksItem()
        # 直接从请求对象中获取URL和referer
        url = failure.request.url
        referer = failure.request.meta.get('referer', '未知referer')  # 提供默认值以防meta中没有referer
        if failure.check(HttpError):
            response = failure.value.response
            item['url'] = url
            item['category'] = self.check_url_category(url)
            item['last_modified'] = None
            item['etag'] = None
            item['is_external'] = self.is_external_link(url)
            item['status_code'] = response.status
            item['referer'] = referer  # 正确获取referer
            yield item