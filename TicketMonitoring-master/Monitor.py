import json
import logging
from time import time

import requests
import urllib3


class Monitor:
    __last_alert_time = 0
    _proxy = None
    # proxy在config.json中配置格式为: {
    #     "http": "http://10.16.10.24:12001",
    #     "https": "http://10.16.10.24:12001"
    #   }
    # 频繁请求请添加代理，自建代理见GitHub: https://github.com/ThinkerWen/ProxyServer

    _bark_keys = []

    def __init__(self):
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        proxy = cfg.get("proxy")
        self._proxy = proxy if proxy else None
        Monitor._bark_keys = cfg.get("notice", {}).get("bark_keys", []) or []
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] : %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

    # IOS用户建议使用Bark提醒，见GitHub: https://github.com/Finb/Bark
    def bark_alert(self, content: str):
        if time() - self.__last_alert_time < 10:
            return
        if not Monitor._bark_keys:
            return
        self.__last_alert_time = time()
        for key in Monitor._bark_keys:
            try:
                requests.get(f"https://api.day.app/{key}/{content}", timeout=5)
            except Exception as e:
                logging.warning(f"Bark 推送失败: {e}")
