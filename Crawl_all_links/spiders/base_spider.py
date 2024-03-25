import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Union, Optional
import scrapy
import re
from Crawl_all_links.config.spider_config import settings
from pybloom_live import BloomFilter
from Crawl_all_links.utils.log_config import logger
class BaseSpider(scrapy.Spider):

    start_urls = [settings.START_URL]

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
            "page_patrol.pipelines.WendengAllSnapShotPipeline": 300
        },
        # 深度限制 无限制
        'DEPTH_LIMIT': settings.DEPTH_LIMIT,
        'DOWNLOAD_DELAY': settings.DOWNLOAD_DELAY,
        'CONCURRENT_REQUESTS': settings.CONCURRENT_REQUESTS,
        'HTTPERROR_ALLOW_ALL': settings.HTTPERROR_ALLOW_ALL,

        'SQLALCHEMY_DB_SETTINGS': {
            # 本地数据库
            'database_url': str(settings.POSTGRES_URL)
        },
    }


    def __init__(self, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.domain = self.get_domain_name(settings.START_URL)
        self.visited_urls = BloomFilter(capacity=1000000, error_rate=0.001)

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
            return 'video'
        elif any(lower_url.endswith(ext) for ext in self.image_extensions):
            return 'image'
        elif any(lower_url.endswith(ext) for ext in self.content_extensions):
            return 'content'
        elif any(lower_url.endswith(ext) for ext in self.document_extensions):
            return 'document'
        elif any(lower_url.endswith(ext) for ext in self.js_extensions):
            return 'js'
        elif any(lower_url.endswith(ext) for ext in self.executable_extensions):
            return 'executable'
        elif any(lower_url.endswith(ext) for ext in self.archive_extensions):
            return 'archive'
        elif any(lower_url.endswith(ext) for ext in self.audio_extensions):
            return 'audio'
        else:
            return 'other'

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

        # 检查传入的日期时间字符串来确定使用的格式
        if ' ' in datetime_str:
            # 如果字符串中包含空格，则假定它包含日期和时间
            fmt = "%Y-%m-%d %H:%M"
        else:
            # 如果没有空格，则假定它仅包含日期
            fmt = "%Y-%m-%d"

        try:
            parsed_datetime = datetime.strptime(datetime_str, fmt)
            return parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"Error parsing datetime string '{datetime_str}' with format '{fmt}'")
            return None

    # 请求头last_modified 的解析
    def parse_datetime_header(self, datetime_bytes, fmt="%a, %d %b %Y %H:%M:%S %Z"):
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