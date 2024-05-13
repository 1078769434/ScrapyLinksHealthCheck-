# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from datetime import datetime

# useful for handling different item types with a single interface

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from Crawl_all_links.utils.log_config import logger
from Crawl_all_links.models.urls import Urls
from sqlalchemy.exc import SQLAlchemyError


class CrawlAllLinksPipeline:
    """
    负责处理爬虫爬取到的链接，并将其存储到数据库中的pipeline。

    属性:
    db_settings (dict): 存储数据库配置的字典。
    engine (sqlalchemy.engine.Engine): SQLAlchemy数据库引擎实例。
    session (sqlalchemy.orm.session.Session): 数据库会话实例。
    """

    def __init__(self, db_settings):
        """
        初始化pipeline。

        参数:
        db_settings (dict): 包含数据库配置信息的字典。
        """
        self.db_settings = db_settings
        self.engine = None
        self.session = None

    @classmethod
    def from_crawler(cls, crawler):
        """
        从爬虫实例中获取pipeline实例。

        参数:
        crawler (scrapy.crawler.Crawler): 爬虫实例。

        返回:
        cls: pipeline的实例。
        """
        db_settings = crawler.settings.getdict('SQLALCHEMY_DB_SETTINGS')
        return cls(db_settings)

    def open_spider(self, spider):
        """
        当爬虫开始运行时调用，用于初始化数据库连接。

        参数:
        spider (scrapy.spiders.Spider): 当前正在运行的爬虫实例。
        """
        self.engine = create_engine(self.db_settings['database_url'])
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def process_item(self, item, spider):
        """
        处理爬虫抓取到的每个项目（item）。

        参数:
        item (scrapy.item.Item): 爬虫抓取到的项目。
        spider (scrapy.spiders.Spider): 当前正在运行的爬虫实例。

        返回:
        scrapy.item.Item: 处理后的项目。
        """
        # 检查项目中是否包含所有必需的字段
        if not all(key in item for key in
                   ['url', 'category', 'status_code', 'etag', 'last_modified', 'is_external', 'referer']):
            logger.error("Missing required field in item.")
            return item  # 缺少必要字段时，直接返回该项目

        try:
            urls = self._create_urls_model(item)  # 创建Urls模型实例
            self._save_to_database(urls)  # 将Urls模型实例保存到数据库
        except SQLAlchemyError as e:
            logger.error(f"Error processing item: {e}")
            self._handle_db_error(e)  # 处理数据库错误
        return item

    def _create_urls_model(self, item):
        """
        根据项目（item）信息创建Urls模型实例。

        参数:
        item (scrapy.item.Item): 爬虫抓取的项目。

        返回:
        Urls: Urls模型实例。
        """
        update_at = datetime.now()  # 获取当前时间，也可以使用last_modified，取决于你的需求
        crawl_at = datetime.now()

        urls = Urls()
        urls.url = item['url']
        urls.category = item['category']
        urls.status_code = item['status_code']
        urls.etag = item['etag']
        urls.last_modified = item['last_modified']
        urls.is_external = item['is_external']
        urls.referer = item['referer']
        urls.crawl_at = crawl_at
        urls.update_at = update_at  # 设置update_at
        return urls

    def _save_to_database(self, urls):
        """
        将Urls模型实例保存到数据库。

        参数:
        urls (Urls): Urls模型实例。
        """
        self.session.add(urls)
        self.session.commit()

    def _handle_db_error(self, e):
        """
        处理数据库操作中的错误。

        参数:
        e (Exception): 异常实例。
        """
        if isinstance(e, IntegrityError):
            logger.error(f"IntegrityError: {e.orig}")
        else:
            logger.error(f"Other DB Error: {e}")
        self.session.rollback()

    def close_spider(self, spider):
        """
        当爬虫关闭时调用，用于清理资源。

        参数:
        spider (scrapy.spiders.Spider): 当前正在关闭的爬虫实例。
        """
        if self.session:
            self.session.close()

        if self.engine:
            # 关闭数据库引擎释放资源
            self.engine.dispose()
