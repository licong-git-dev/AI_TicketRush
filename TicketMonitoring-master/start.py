"""
TicketRush 监控守护进程。

进化点（vs 原版）：
- 启动自检：每个监控对象先执行一次 monitor()，token/show_id 错的立刻爆出来
- 心跳：每 5 分钟打印一行总状态（哪些监控在跑、最近成功时间、累计回流次数）
- 自适应频率：默认 30s 一轮；越接近 deadline 越快（最低 5s）
- 失败回退：连续失败 N 次会跳过该监控并通过 Telegram/邮件告警
- 通知通道：Telegram 优先（实时），邮件兜底，Bark 可选
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional, Union

from Monitor_DM import DM
from Monitor_FWD import FWD
from Monitor_MY import MY
from Monitor_PXQ import PXQ
from email_notifier import EmailNotifier
from telegram_notifier import TelegramNotifier
from serverchan_notifier import ServerChanNotifier, FeishuNotifier


PLATFORM_MAP = {0: ("大麦", DM), 1: ("猫眼", MY), 2: ("纷玩岛", FWD), 3: ("票星球", PXQ)}


def get_task(show: dict) -> Optional[Union[DM, MY, FWD, PXQ]]:
    plat = show.get("platform")
    if plat not in PLATFORM_MAP:
        logging.error(f"未知 platform={plat}, show={show.get('show_name')}")
        return None
    name, cls = PLATFORM_MAP[plat]
    try:
        return cls(show)
    except Exception as e:
        logging.error(f"{name} {show.get('show_name')} 加载失败：{e}")
        return None


def adaptive_interval(deadline: datetime) -> float:
    """距 deadline 越近轮询越快"""
    remaining = (deadline - datetime.now()).total_seconds()
    if remaining < 0:
        return -1
    if remaining < 60:        # 开抢前 1 分钟内：每秒
        return 1
    if remaining < 600:       # 10 分钟内：5 秒
        return 5
    if remaining < 3600:      # 1 小时内：15 秒
        return 15
    return 30                 # 远期：30 秒


class Stats:
    def __init__(self, show_name: str, platform: str):
        self.show_name = show_name
        self.platform = platform
        self.checks = 0
        self.successes = 0
        self.failures = 0
        self.consec_failures = 0
        self.last_success_at: Optional[datetime] = None
        self.last_error: str = ""
        self.alerts_fired = 0
        self.skipped = False


class Runner:
    CONSEC_FAIL_THRESHOLD = 5

    def __init__(self):
        with open("config.json", "r", encoding="utf-8") as f:
            self.cfg = json.load(f)
        self.email_notifier = EmailNotifier()
        self.telegram_notifier = TelegramNotifier()
        self.serverchan_notifier = ServerChanNotifier()
        self.feishu_notifier = FeishuNotifier()
        self.threadPool = ThreadPoolExecutor(max_workers=20, thread_name_prefix="ticket_monitor_")
        self.stats: dict[str, Stats] = {}
        self._stop = False

    # ---------- 启动自检 ----------
    def healthcheck(self, monitors: list) -> bool:
        ok_total = 0
        for monitor, show in monitors:
            stats = self.stats[show["show_name"]]
            try:
                result = monitor.monitor()
                stats.checks += 1
                stats.successes += 1
                stats.last_success_at = datetime.now()
                logging.info(
                    f"✅ 自检通过：{stats.platform} {stats.show_name} 当前可买 {len(result)} 档"
                )
                ok_total += 1
            except Exception as e:
                stats.checks += 1
                stats.failures += 1
                stats.last_error = str(e)[:200]
                logging.error(f"❌ 自检失败：{stats.platform} {stats.show_name} → {stats.last_error}")
        # 通知通道自检
        channels_active = []
        for name, n in [
            ("Telegram", self.telegram_notifier),
            ("Server 酱", self.serverchan_notifier),
            ("飞书", self.feishu_notifier),
        ]:
            if not n.enabled:
                continue
            err = n.healthcheck()
            if err and err != "未配置":
                logging.warning(f"⚠️  {name} 通道异常：{err}")
            else:
                logging.info(f"✅ {name} 通道就绪")
                channels_active.append(name)
        if self.email_notifier.config.get("notice", {}).get("email"):
            channels_active.append("邮件")
        if not channels_active:
            logging.error("⛔ 没有任何通知通道可用，回流告警将丢失！至少配置一个：Telegram / Server 酱 / 飞书 / 邮件")
        else:
            self._broadcast(f"🚀 TicketRush 监控启动 · 通道：{'+'.join(channels_active)}")
        return ok_total > 0

    def _broadcast(self, text: str):
        """所有可用通道一起发"""
        try:
            self.telegram_notifier.send(text)
        except Exception as e:
            logging.debug(f"telegram broadcast failed: {e}")
        try:
            self.serverchan_notifier.send("TicketRush", text)
        except Exception as e:
            logging.debug(f"serverchan broadcast failed: {e}")
        try:
            self.feishu_notifier.send(text)
        except Exception as e:
            logging.debug(f"feishu broadcast failed: {e}")

    # ---------- 单监控循环 ----------
    def loop_monitor(self, monitor, show: dict) -> None:
        stats = self.stats[show["show_name"]]
        deadline = datetime.strptime(show["deadline"], "%Y-%m-%d %H:%M:%S")

        while not self._stop and datetime.now() < deadline and not stats.skipped:
            interval = adaptive_interval(deadline)
            if interval < 0:
                break
            try:
                stock = monitor.monitor()
                stats.checks += 1
                stats.successes += 1
                stats.consec_failures = 0
                stats.last_success_at = datetime.now()
                if stock:
                    self.fire_alert(stats, stock)
            except Exception as e:
                stats.checks += 1
                stats.failures += 1
                stats.consec_failures += 1
                stats.last_error = str(e)[:200]
                logging.warning(
                    f"{stats.platform} {stats.show_name} 第 {stats.consec_failures} 次失败：{stats.last_error}"
                )
                if stats.consec_failures >= self.CONSEC_FAIL_THRESHOLD:
                    stats.skipped = True
                    msg = (
                        f"🛑 {stats.platform} {stats.show_name} 连续失败 "
                        f"{self.CONSEC_FAIL_THRESHOLD} 次，已停止监控。"
                        f"最后错误：{stats.last_error}（多半是 token 过期）"
                    )
                    logging.error(msg)
                    self.telegram_notifier.send(msg)
                    break
            time.sleep(interval)

    def fire_alert(self, stats: Stats, stock: list):
        stats.alerts_fired += 1
        text = (
            f"🎫 回流啦！{stats.platform} 《{stats.show_name}》共 {len(stock)} 档可买，"
            f"立即下单：{datetime.now():%H:%M:%S}"
        )
        ident = f"{stats.platform}_{stats.show_name}"
        # 实时通道：Telegram / Server 酱 / 飞书 全发
        for n, label in [
            (self.telegram_notifier, "telegram"),
            (self.serverchan_notifier, "serverchan"),
            (self.feishu_notifier, "feishu"),
        ]:
            try:
                if n.should_send(ident):
                    if label == "serverchan":
                        n.send(f"回流·{stats.platform}·{stats.show_name}", text)
                    else:
                        n.send(text)
            except Exception as e:
                logging.warning(f"{label} 推送异常：{e}")
        # 邮件兜底
        if self.email_notifier.should_send(ident):
            try:
                self.email_notifier.send_notification(
                    stats.show_name, f"Ticket Alert: {stats.show_name}", text
                )
            except Exception as e:
                logging.warning(f"邮件推送异常：{e}")
        # Bark（如配了）
        try:
            from Monitor import Monitor as _M
            _M().bark_alert(text)
        except Exception:
            pass
        logging.info(text)

    # ---------- 心跳：每 5 分钟报一次总账 ----------
    def heartbeat_loop(self) -> None:
        while not self._stop:
            time.sleep(300)
            self.print_heartbeat()

    def print_heartbeat(self):
        lines = ["💓 心跳报告"]
        for s in self.stats.values():
            last = s.last_success_at.strftime("%H:%M:%S") if s.last_success_at else "从未"
            status = "🛑跳过" if s.skipped else "🟢运行"
            lines.append(
                f"  {status} {s.platform} {s.show_name} | "
                f"检查 {s.checks} 成功 {s.successes} 失败 {s.failures} | "
                f"回流告警 {s.alerts_fired} 次 | 最近成功 {last}"
            )
        report = "\n".join(lines)
        logging.info(report)

    # ---------- 入口 ----------
    def start(self):
        shows = self.cfg.get("monitor_list", [])
        if not shows:
            logging.error("config.json 没有任何监控对象")
            return

        # 1. 加载所有 monitor
        monitors = []
        for show in shows:
            self.stats[show["show_name"]] = Stats(
                show["show_name"], PLATFORM_MAP.get(show.get("platform"), ("?", None))[0]
            )
            task = get_task(show)
            if task:
                monitors.append((task, show))

        if not monitors:
            logging.error("没有任何监控对象加载成功，请检查 token / show_id")
            return

        # 2. 启动自检
        logging.info(f"开始自检 {len(monitors)} 个监控对象……")
        if not self.healthcheck(monitors):
            logging.error("⛔ 全部自检失败，程序退出。请重新抓 token / 检查 show_id。")
            return

        # 3. 心跳
        self.threadPool.submit(self.heartbeat_loop)

        # 4. 监控
        for monitor, show in monitors:
            if not self.stats[show["show_name"]].skipped:
                self.threadPool.submit(self.loop_monitor, monitor, show)

        try:
            self.threadPool.shutdown(wait=True)
        except KeyboardInterrupt:
            self._stop = True
            logging.info("用户中断，停止监控……")
            self.print_heartbeat()


if __name__ == '__main__':
    Runner().start()
