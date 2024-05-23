import logging

from urllib.parse import urlparse

import scrapy
import re

from Crawl_all_links import config
from Crawl_all_links.utils.page_type import PageType
from scrapy import signals

import re
from datetime import datetime

from pybloom_live import BloomFilter
from Crawl_all_links.utils.log_config import logger


class BaseSpider(scrapy.Spider):
    start_urls = [config.START_URL]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    }

    # 文章类型
    content_extensions = ['.html']

    # 视频文件后缀
    video_extensions = [
        '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.webm', '.mkv', '.mpeg', '.ogg', '.3gp',
        '.ts', '.rm', '.rmvb', '.avchd'
    ]
    # 文档文件后缀
    document_extensions = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
        '.rtf', '.csv', '.html', '.xml', '.json', '.odt', '.ods', '.odp'
    ]
    # 脚本文件后缀
    js_extensions = [
        '.js', '.jsx', '.mjs'
    ]
    # 可执行文件后缀
    executable_extensions = [
        '.exe', '.apk', '.dmg', '.msi', '.app'
    ]
    # 压缩文件后缀
    archive_extensions = [
        '.zip', '.rar', '.tar', '.tar.gz', '.taz'
    ]
    # 音频文件后缀
    audio_extensions = [
        '.mp3', '.wav', '.ogg', '.m4a', '.flac'
    ]
    # 图片文件后缀
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp']

    custom_settings = {
        'ITEM_PIPELINES': {
            "Crawl_all_links.import_pg_db.pipelines.CrawlAllLinksPipeline": 300
        },
        # 深度限制 无限制
        'DEPTH_LIMIT': config.DEPTH_LIMIT,
        'DOWNLOAD_DELAY': config.DOWNLOAD_DELAY,
        'CONCURRENT_REQUESTS': config.CONCURRENT_REQUESTS,
        'HTTPERROR_ALLOW_ALL': config.HTTPERROR_ALLOW_ALL,
        'DEPTH_STATS_VERBOSE': True,
        'SQLALCHEMY_DB_SETTINGS': {
            # 本地数据库
            'database_url': str(config.settings.POSTGRES_URL)
        },
    }

    def __init__(self, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.domain = self.get_domain_name(config.START_URL)
        self.visited_urls = BloomFilter(capacity=1000000, error_rate=0.001)
        # 添加月份名称到数字的映射
        self.month_numbers = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
    # @classmethod
    # def from_crawler(cls, crawler, *args, **kwargs):
    #     """
    #     从爬虫实例中创建一个Spider实例。
    #
    #     :param cls: 类方法的约定参数，指代当前类。
    #     :param crawler: 从该crawler实例中创建Spider。
    #     :param args: 位置参数，传递给Spider构造函数。
    #     :param kwargs: 关键字参数，传递给Spider构造函数。
    #     :return: 返回一个初始化的Spider实例。
    #     """
    #     spider = super(BaseSpider, cls).from_crawler(crawler, *args, **kwargs)
    #     # 连接spider_closed信号，当爬虫关闭时执行指定的函数
    #     """
    #     该函数是Scrapy爬虫框架中的一个连接函数，用于将spider_closed信号与spider对象的spider_closed方法连接起来。
    #     当爬虫关闭时，会触发spider_closed信号，此时会调用spider对象的spider_closed方法。
    #     这样可以在爬虫关闭时执行一些必要的清理工作。
    #     """
    #     crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
    #     return spider
    #
    # def spider_closed(self, spider):
    #     """
    #     当Spider关闭时执行的操作。
    #
    #     :param spider: 关闭的Spider实例。
    #     """
    #     # 记录Spider关闭信息
    #     spider.logger.info("Spider closed: %s", spider.name)

    def clean_content(self, content: str) -> str:
        """
        清洗内容中的多余字符和标签。

        参数:
        - content: 需要清洗的原始内容字符串。

        返回值:
        - 清洗后的字符串，移除了多余的空格、制表符、换行符、HTML标签等。
        """
        # 移除多余的空格、制表符、换行符、以及HTML中的一些特殊字符和空白字符
        content = re.sub(
            r'[\n\r\t ]+|&nbsp;|\u3000|\xa0|\u200B|\u200C|\u200D|\uFEFF|&lt;|&gt;|&amp;|&quot;|&#39;|<br>|<br/>|<p>|</p>|&emsp;',
            '', content)
        # 移除所有的HTML标签
        content = re.sub(r'<[^>]+>', '', content)
        return content

    def check_url_category(self, lower_url: str) -> str:
        if any(lower_url.endswith(ext) for ext in self.video_extensions):
            return PageType.VIDEO.value
        elif any(lower_url.endswith(ext) for ext in self.image_extensions):
            return PageType.IMAGE.value
        elif any(lower_url.endswith(ext) for ext in self.content_extensions):
            return PageType.CONTENT.value
        elif any(lower_url.endswith(ext) for ext in self.document_extensions):
            return PageType.DOCUMENT.value
        elif any(lower_url.endswith(ext) for ext in self.js_extensions):
            return PageType.JS.value
        elif any(lower_url.endswith(ext) for ext in self.executable_extensions):
            return PageType.EXECUTABLE.value
        elif any(lower_url.endswith(ext) for ext in self.archive_extensions):
            return PageType.ARCHIVE.value
        elif any(lower_url.endswith(ext) for ext in self.audio_extensions):
            return PageType.AUDIO.value
        else:
            return PageType.OTHER.value

    def extract_keywords(self, response):
        """
        尝试从给定的response中提取关键词。
        如果提取失败或发生异常，则返回'无关键词'。

        :param response: Scrapy的response对象
        :return: 提取到的关键词字符串
        """
        try:
            # 尝试从meta标签'keywords'中提取关键词
            keywords = response.xpath("/html/head/meta[@name='keywords']/@content").extract_first()
            return keywords or '无关键词'
        except Exception as e:
            # 记录异常信息
            logging.error(f"Error extracting keywords: {e}")
            return '无关键词'


    def parse_datetime(self, datetime_str):
        if not datetime_str:
            return None

        # 检查日期时间字符串的格式
        if 'GMT' in datetime_str:
            fmt = "%a, %d %b %Y %H:%M:%S %Z"
        elif ' ' in datetime_str:
            fmt = "%Y-%m-%d %H:%M"
        else:
            fmt = "%Y-%m-%d"

        try:
            parsed_datetime = datetime.strptime(datetime_str, fmt)
            # 如果需要统一输出格式，可以使用以下代码
            return parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            match = re.match(r'^\w{3}, (\d{2}) (\w{3}) (\d{4}) (\d{2}):(\d{2}):(\d{2}) GMT$', datetime_str)
            if match:
                # 如果日期时间字符串是' Sat, 12 Dec 2020 12:45:45 GMT'格式，尝试转换
                day, month, year, hour, minute, second = map(int, match.groups())
                parsed_datetime = datetime(year, self.month_numbers[month], day, hour, minute, second)
                return parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
            else:
                print(f"Error parsing datetime string '{datetime_str}' with format '{fmt}'")
                return None




    # 请求头last_modified 的解析
    def parse_datetime_header(self, datetime_bytes):
        try:
            return self.parse_datetime(datetime_bytes.decode())
        except (AttributeError, ValueError):
            return None

    # 请求头etag解析
    def extract_header(self, response, header_name):
        try:
            header_value = response.headers.get(header_name).decode().replace('W/', '').replace("''", '')
            return header_value or None
        except AttributeError:
            return None

    def get_domain_name(self, url):
        """
        根据给定的 URL 返回其主域名。

        :param url: 要处理的 URL 字符串
        :return: URL 的主域名，如果 URL 无效则返回 None
        """
        try:
            parsed_url = urlparse(url)
            domain_name = '{uri.netloc}'.format(uri=parsed_url)
            return domain_name if domain_name else None
        except Exception as e:
            print(f"Error parsing URL '{url}': {e}")
            return None

    def is_external_link(self, url: str) -> bool:
        """
        检查给定的URL是否为外链。

        参数:
        url (str): 要检查的URL。

        返回:
        bool: 如果URL是外链，则为True；否则为False。
        """
        parsed_url = urlparse(url)
        if parsed_url.netloc == self.domain:
            return False
        else:
            return True

    def process_referer(self, referer_header):
        if referer_header:
            try:
                return referer_header.decode('utf-8')
            except Exception as e:
                logger.error(f"Error decoding referer header: {e}")
        return None
