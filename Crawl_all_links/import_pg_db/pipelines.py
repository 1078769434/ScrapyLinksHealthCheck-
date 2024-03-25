# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from Crawl_all_links.utils.log_config import logger
from Crawl_all_links.models.urls import Urls

class CrawlAllLinksPipeline:
    def __init__(self, db_settings):
        self.db_settings = db_settings

    @classmethod
    def from_crawler(cls, crawler):
        db_settings = crawler.settings.getdict('SQLALCHEMY_DB_SETTINGS')
        return cls(db_settings)

    def open_spider(self, spider):
        self.engine = create_engine(self.db_settings['database_url'])
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def process_item(self, item, spider):

        urls = Urls()
        urls.url = item['url']
        urls.category = item['category']
        urls.status_code = item['status_code']
        urls.etag = item['etag']
        urls.last_modified = item['last_modified']
        urls.is_external = item['is_external']
        urls.referer = item['referer']

        # 将模型实例添加到会话并提交
        self.session.add(urls)
        try:
            self.session.commit()
        except IntegrityError as e:
            logger.error(e)
            self.session.rollback()

        return item

    def close_spider(self, spider):
        self.session.close()
