from scrapy import cmdline


def run_scrapy_project():
    # 运行爬虫
    cmdline.execute("scrapy crawl Link_detection".split())


def run_scrapy_project_continue():
    # 断点续爬
    cmdline.execute("scrapy crawl Link_detection -s JOBDIR=crawls/first".split())


if __name__ == "__main__":
    run_scrapy_project()
