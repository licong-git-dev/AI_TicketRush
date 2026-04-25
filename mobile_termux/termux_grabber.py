#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Termux 手机端抢票脚本（统一版）

用法：
  1. Termux 安装：pkg install python && pip install uiautomator2
  2. 在被控手机开启 USB 调试（或 ADB over Wi-Fi）
  3. 首次初始化：python -c "import uiautomator2 as u2; u2.connect().healthcheck()"
  4. 编辑本目录下 config.json，填写 target_date / target_tickets
  5. 运行：python termux_grabber.py
  6. 切到猫眼 App 演出详情页即可

配置全部来自 config.json，脚本本身不要改。
"""

import json
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

try:
    import uiautomator2 as u2
except ImportError:
    sys.exit("缺少 uiautomator2，请先执行：pip install uiautomator2")


CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"找不到配置文件：{CONFIG_PATH}")
    with CONFIG_PATH.open(encoding="utf-8") as f:
        cfg = json.load(f)

    required = ["target_date", "target_tickets", "keywords"]
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        sys.exit(f"config.json 缺少字段：{missing}")
    if "示例" in cfg["target_date"]:
        sys.exit("config.json 的 target_date 还是示例值，请先替换为真实场次文本")
    return cfg


class Grabber:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.kw = cfg["keywords"]
        self.device = None
        self.start = time.time()
        self.last_action = time.time()
        self.action_count = 0

        self.click_interval = 1.0 / max(1, int(cfg.get("click_rate_per_sec", 8)))
        self.click_burst = int(cfg.get("click_burst_max", 20))
        self.max_runtime = int(cfg.get("max_runtime_sec", 900))
        self.max_inactivity = int(cfg.get("max_inactivity_sec", 300))

        stamp = datetime.now().strftime("%m%d_%H%M")
        self.log_path = Path(f"/sdcard/抢票日志_{stamp}.txt")

    def log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def connect(self) -> bool:
        try:
            self.device = u2.connect()
            self.device.settings["operation_delay"] = (0.1, 0.2)
            self.device.settings["operation_delay_methods"] = ["click", "swipe"]
            info = self.device.info
            self.log(f"已连接：{info.get('productName')} Android {info.get('version')}")
            return True
        except Exception as e:
            self.log(f"设备连接失败：{e}", "ERROR")
            return False

    def find(self, keywords, exact=False):
        for kw in keywords:
            try:
                elem = self.device(text=kw) if exact else self.device(textContains=kw)
                if elem.exists():
                    return elem, kw
                elem = self.device(description=kw) if exact else self.device(descriptionContains=kw)
                if elem.exists():
                    return elem, kw
            except Exception:
                continue
        return None, None

    def click(self, elem, desc: str) -> bool:
        for attempt in range(3):
            try:
                if elem.exists():
                    elem.click()
                    self.action_count += 1
                    self.last_action = time.time()
                    self.log(f"{desc} 已点击")
                    time.sleep(self.click_interval)
                    return True
            except Exception as e:
                self.log(f"{desc} 点击异常 {attempt+1}/3: {e}", "WARN")
                time.sleep(0.3)
        return False

    def burst_click(self, elem, desc: str) -> bool:
        self.log(f"{desc} 进入连击模式（上限 {self.click_burst} 次）")
        n = 0
        for _ in range(self.click_burst):
            try:
                if not elem.exists():
                    break
                elem.click()
                n += 1
                time.sleep(self.click_interval)
            except Exception:
                break
        self.action_count += n
        self.last_action = time.time()
        self.log(f"{desc} 连击完成 {n} 次")
        return n > 0

    def countdown(self):
        try:
            src = self.device.dump_hierarchy()
            for p in [r"(\d+天\d+时\d+分\d+秒)", r"(\d+:\d+:\d+)", r"(\d+小时\d+分钟)"]:
                m = re.search(p, src)
                if m:
                    return m.group(1)
        except Exception:
            pass
        return None

    def step_pay(self) -> bool:
        elem, kw = self.find(self.kw["pay"])
        if elem:
            self.log(f"🎉 到达支付页：{kw}，请手动完成支付")
            return True
        return False

    def step_submit(self) -> bool:
        elem, kw = self.find(self.kw["submit"])
        if elem:
            return self.burst_click(elem, f"提交订单({kw})")
        return False

    def step_confirm(self) -> bool:
        elem, kw = self.find(self.kw["confirm"])
        if elem:
            return self.click(elem, f"确认({kw})")
        return False

    def step_ticket(self) -> bool:
        for t in self.cfg["target_tickets"]:
            elem, _ = self.find([t], exact=True)
            if elem:
                return self.click(elem, f"票档 {t}")
        return False

    def step_date(self) -> bool:
        elem, _ = self.find([self.cfg["target_date"]], exact=True)
        if elem:
            return self.click(elem, f"场次 {self.cfg['target_date']}")
        return False

    def step_buy(self) -> bool:
        elem, kw = self.find(self.kw["buy"])
        if elem:
            return self.click(elem, f"购买按钮({kw})")
        return False

    def step_refresh(self) -> bool:
        elem, kw = self.find(self.kw["refresh"])
        if elem:
            return self.click(elem, f"刷新({kw})")
        return False

    def run(self):
        self.log("=" * 50)
        self.log("Termux 抢票启动")
        self.log(f"目标场次：{self.cfg['target_date']}")
        self.log(f"票档数量：{len(self.cfg['target_tickets'])}")
        self.log(f"点击频率：{1/self.click_interval:.1f} 次/秒")
        self.log(f"日志：{self.log_path}")
        self.log("=" * 50)

        if not self.connect():
            return

        try:
            while True:
                now = time.time()
                if now - self.start > self.max_runtime:
                    self.log("达到最大运行时间，退出", "WARN")
                    break
                if now - self.last_action > self.max_inactivity:
                    self.log("长时间无操作，退出", "WARN")
                    break

                cd = self.countdown()
                if cd:
                    reserved, _ = self.find(self.kw["reservation"])
                    if reserved:
                        self.log(f"倒计时 {cd}，已预约，持续监听")
                        self.last_action = now
                        time.sleep(2)
                        continue
                    self.log(f"倒计时 {cd}")

                if self.step_pay():
                    break
                if self.step_submit():
                    continue
                if self.step_confirm():
                    continue
                if self.step_ticket():
                    continue
                if self.step_date():
                    continue
                if self.step_buy():
                    continue

                elapsed = int(now - self.last_action)
                if elapsed and elapsed % 15 == 0:
                    self.step_refresh()
                time.sleep(1)

        except KeyboardInterrupt:
            self.log("用户中断")
        except Exception as e:
            self.log(f"异常：{e}\n{traceback.format_exc()}", "ERROR")
        finally:
            total = int(time.time() - self.start)
            self.log(f"结束：运行 {total}s，累计 {self.action_count} 次操作")


if __name__ == "__main__":
    Grabber(load_config()).run()
