from abc import ABC, abstractmethod

import requests

from Crawl_all_links import config
from Crawl_all_links.proxy.proxy_ip_provider import IpGetError

from typing import Dict, List
from urllib.parse import urlencode

from Crawl_all_links.tools import utils

class ProxyProvider(ABC):
    @abstractmethod
    async def get_proxies(self, num: int) -> List[Dict]:
        """
        获取 IP 的抽象方法，不同的 HTTP 代理商需要实现该方法
        :param num: 提取的 IP 数量
        :return:
        """
        pass


#快代理隧道代理
class KuaiDaiLiHttpProxy(ProxyProvider):
    username = config.settings.KUAIDAILI_USERNAME
    password = config.settings.KUAIDAILI_PASSWORD

    def __init__(self, secret_id: str, signature: str, num: int = 1):
        self.proxy_brand_name = "KuaiDaiLiHTTP"
        self.api_path = "https://tps.kdlapi.com/api"
        self.params = {
            "secret_id": secret_id,
            "signature": signature,
            "num": num,
            "format": "json",  # 数据结果为json
        }

    def get_proxies(self, num: int):
        """
        获取代理IP列表。
        :param num: 需要获取的代理IP数量。
        """
        try:
            # 构建请求URL并发送GET请求获取IP代理信息
            self.params["num"] = num
            url = self.api_path + "/gettps" + '?' + urlencode(self.params)
            utils.logger.info(f"[JiSuHttpProxy.get_proxies] get ip proxy url:{url}")
            response = requests.get(url)

            # 处理API响应，将获取到的IP代理信息处理并存储
            res_dict: Dict = response.json()
            proxy_url_list = []
            if res_dict.get("code") == 0:
                data = res_dict.get("data")
                tunnel_list = data.get("proxy_list")
                for tunnel in tunnel_list:
                    proxy_url = "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": self.username, "pwd": self.password,
                                                                        "proxy": tunnel}
                    proxy_url_list.append(proxy_url)
            else:
                # 当API响应错误时，抛出自定义异常
                raise IpGetError(res_dict.get("msg", "unkown err"))

        except requests.exceptions.RequestException as e:
            utils.logger.error(f"[JiSuHttpProxy.get_proxies] Request error: {str(e)}")
            raise IpGetError("Request failed")

        return proxy_url_list


IpProxy_2 = KuaiDaiLiHttpProxy(
    secret_id=config.settings.SECRET_ID,
    signature=config.settings.SIGNATURE,
    num=1
)

if __name__ == '__main__':
    proxy_url = IpProxy_2.get_proxies(2)
    print(proxy_url)
