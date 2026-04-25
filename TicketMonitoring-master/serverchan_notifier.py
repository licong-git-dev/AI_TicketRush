"""
Server 酱（含 Server 酱·Turbo / WxPusher / 飞书 webhook）通知通道。

为什么加：
- Telegram 在国内需要梯子，不是所有人都能用
- Server 酱 Turbo 是免费的微信推送方案，注册扫码登录即拿 SendKey
- 飞书 webhook 适合团队场景

config.json 格式：
{
  "notice": {
    "serverchan": {
      "send_keys": ["SCT123456..."]
    },
    "feishu_webhooks": [
      "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
    ]
  }
}
"""

import json
import logging
import time
from typing import Dict, List


class ServerChanNotifier:
    """Server 酱 Turbo：https://sct.ftqq.com 微信扫码即用"""

    API = "https://sctapi.ftqq.com/{key}.send"
    MIN_INTERVAL_SEC = 5

    def __init__(self, config_path: str = "config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        sc = cfg.get("notice", {}).get("serverchan", {}) or {}
        self.send_keys: List[str] = sc.get("send_keys") or []
        self.enabled = bool(self.send_keys)
        self._last_sent: Dict[str, float] = {}

    def should_send(self, identifier: str) -> bool:
        if not self.enabled:
            return False
        now = time.time()
        if now - self._last_sent.get(identifier, 0) < self.MIN_INTERVAL_SEC:
            return False
        self._last_sent[identifier] = now
        return True

    def send(self, title: str, content: str = "") -> bool:
        if not self.enabled:
            return False
        try:
            import requests
        except ImportError:
            return False
        ok = True
        for key in self.send_keys:
            try:
                r = requests.post(
                    self.API.format(key=key),
                    data={"title": title[:32], "desp": content or title},
                    timeout=5,
                )
                if r.status_code != 200 or r.json().get("code") != 0:
                    logging.warning(f"Server 酱推送失败: {r.status_code} {r.text[:200]}")
                    ok = False
            except Exception as e:
                logging.warning(f"Server 酱推送异常: {e}")
                ok = False
        return ok

    def healthcheck(self) -> str:
        if not self.enabled:
            return "未配置"
        # Server 酱没有"测试"接口，发一条静默心跳验证
        return ""


class FeishuNotifier:
    """飞书自定义 webhook：群里加机器人 → 拿 webhook URL"""

    MIN_INTERVAL_SEC = 5

    def __init__(self, config_path: str = "config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.webhooks: List[str] = cfg.get("notice", {}).get("feishu_webhooks") or []
        self.enabled = bool(self.webhooks)
        self._last_sent: Dict[str, float] = {}

    def should_send(self, identifier: str) -> bool:
        if not self.enabled:
            return False
        now = time.time()
        if now - self._last_sent.get(identifier, 0) < self.MIN_INTERVAL_SEC:
            return False
        self._last_sent[identifier] = now
        return True

    def send(self, text: str) -> bool:
        if not self.enabled:
            return False
        try:
            import requests
        except ImportError:
            return False
        ok = True
        for url in self.webhooks:
            try:
                r = requests.post(
                    url,
                    json={"msg_type": "text", "content": {"text": text}},
                    timeout=5,
                )
                if r.status_code != 200:
                    logging.warning(f"飞书推送失败: {r.status_code}")
                    ok = False
            except Exception as e:
                logging.warning(f"飞书推送异常: {e}")
                ok = False
        return ok

    def healthcheck(self) -> str:
        return "" if self.enabled else "未配置"
