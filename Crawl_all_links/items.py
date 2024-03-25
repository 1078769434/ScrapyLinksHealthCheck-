# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CrawlAllLinksItem(scrapy.Item):

    #页面地址
    url = scrapy.Field()
    #页面分类
    # content, image, image other
    category = scrapy.Field()


    #状态码
    status_code = scrapy.Field()

    #生成给定页面内容的ETag headers
    etag = scrapy.Field()

    #页面最后修改时间 headers
    last_modified = scrapy.Field()

    #是否为外链
    is_external = scrapy.Field()


    #父页面
    referer = scrapy.Field()
