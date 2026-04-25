"""
Telegram 实时推送通道。

为什么选 Telegram：
- 跨 iOS/Android/桌面，无平台限制（Bark 只 iOS）
- 推送延迟 < 1 秒（邮件 5+ 分钟）
- 免费，无频次限制
- bot 创建只需 30 秒：BotFather → /newbot → 拿 token；启动 bot 发一条消息 → 调
  https://api.telegram.org/bot<TOKEN>/getUpdates 拿 chat_id

config.json 格式：
{
  "notice": {
    "telegram": {
      "bot_token": "123456:ABC...",
      "chat_ids": ["123456789"]
    }
  }
}
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List


class TelegramNotifier:
    API = "https://api.telegram.org/bot{token}/sendMessage"
    MIN_INTERVAL_SEC = 5

    def __init__(self, config_path: str = "config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        tg = cfg.get("notice", {}).get("telegram", {}) or {}
        self.bot_token = tg.get("bot_token") or ""
        self.chat_ids: List[str] = tg.get("chat_ids") or []
        self.enabled = bool(self.bot_token and self.chat_ids)
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
            logging.error("缺少 requests，无法发送 Telegram 通知")
            return False

        url = self.API.format(token=self.bot_token)
        ok = True
        for chat_id in self.chat_ids:
            try:
                r = requests.post(
                    url,
                    json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
                    timeout=5,
                )
                if r.status_code != 200:
                    logging.warning(f"Telegram 推送失败 {chat_id}: {r.status_code} {r.text[:200]}")
                    ok = False
            except Exception as e:
                logging.warning(f"Telegram 推送异常 {chat_id}: {e}")
                ok = False
        return ok

    def healthcheck(self) -> str:
        """返回空串=OK，否则返回错误说明"""
        if not self.enabled:
            return "未配置"
        try:
            import requests
            r = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/getMe", timeout=5
            )
            if r.status_code != 200:
                return f"bot_token 无效（{r.status_code}）"
            return ""
        except Exception as e:
            return f"网络异常：{e}"


if __name__ == "__main__":
    # 测试用：python telegram_notifier.py
    import sys
    n = TelegramNotifier()
    if not n.enabled:
        sys.exit("未配置 Telegram，编辑 config.json 的 notice.telegram")
    err = n.healthcheck()
    if err:
        sys.exit(f"健康检查失败：{err}")
    print("健康检查通过，发送测试消息……")
    if n.send("✅ TicketRush Telegram 通道已就绪"):
        print("发送成功")
    else:
        sys.exit("发送失败，看日志")
