# 爬虫基础配置


# #起始url
START_URL: str = "http://www.wendeng.gov.cn/col/col79327/index.html"
# #爬虫深度
DEPTH_LIMIT: int = 0
# #爬虫延时
DOWNLOAD_DELAY: int = 0

HTTPERROR_ALLOW_ALL: bool = True
# #并发请求
CONCURRENT_REQUESTS: int = 5