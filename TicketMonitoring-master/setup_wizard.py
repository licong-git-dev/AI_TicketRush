"""
交互式向导：把 config.json 写好，无需手改。

跑：python setup_wizard.py
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs


CFG_PATH = Path(__file__).parent / "config.json"
EXAMPLE_PATH = Path(__file__).parent / "config.json.example"

PLATFORMS = {
    "1": ("猫眼", 1),
    "2": ("大麦", 0),
    "3": ("纷玩岛", 2),
    "4": ("票星球", 3),
}


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default


def ask_yes(prompt: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    val = input(f"{prompt} [{d}]: ").strip().lower()
    if not val:
        return default
    return val.startswith("y")


def extract_show_id(url_or_id: str, platform: int) -> str:
    """从演出 URL 或 ID 字符串提取数字 ID"""
    s = url_or_id.strip()
    if s.isdigit():
        return s
    try:
        parsed = urlparse(s)
        qs = parse_qs(parsed.query)
        # 猫眼 H5: i.maoyan.com/wx/album.html?id=12345
        if "id" in qs:
            return qs["id"][0]
        if "projectId" in qs:
            return qs["projectId"][0]
        # 大麦: m.damai.cn/shows/item.html?itemId=760167213815
        if "itemId" in qs:
            return qs["itemId"][0]
        # 路径里的数字段
        m = re.search(r"/(\d{5,})(?:[/?#]|$)", parsed.path)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""


def add_show(existing: list) -> dict:
    print("\n— 添加监控演出 —")
    for k, (name, _) in PLATFORMS.items():
        print(f"  {k}. {name}")
    while True:
        choice = ask("选择平台编号", "1")
        if choice in PLATFORMS:
            break
        print("无效编号")
    plat_name, plat_code = PLATFORMS[choice]

    while True:
        url_or_id = ask(f"{plat_name} 演出 URL 或 show_id")
        sid = extract_show_id(url_or_id, plat_code)
        if sid:
            print(f"  → 解析出 show_id = {sid}")
            break
        print("没识别出 ID，再试一次（也可直接粘数字 ID）")

    show_name = ask("起个备注名（自己看）")
    deadline = ask("监控截止时间", "2027-01-01 00:00:00")
    return {
        "show_id": sid,
        "show_name": show_name or f"{plat_name}-{sid}",
        "platform": plat_code,
        "deadline": deadline,
    }


def collect_telegram() -> dict:
    print("\n— Telegram（实时推送，跨平台；国内需梯子） —")
    print("  Telegram 找 @BotFather → /newbot → 拿 bot_token")
    print("  和 bot 发一条消息后访问：https://api.telegram.org/bot<TOKEN>/getUpdates")
    print("  里面 message.chat.id 就是 chat_id\n")
    if not ask_yes("配 Telegram？", False):
        return {"bot_token": "", "chat_ids": []}
    bot = ask("bot_token")
    chat = ask("chat_id（多个逗号分隔）")
    return {"bot_token": bot, "chat_ids": [c.strip() for c in chat.split(",") if c.strip()]}


def collect_serverchan() -> dict:
    print("\n— Server 酱 Turbo（推荐国内：微信扫码即拿 SendKey） —")
    print("  访问 https://sct.ftqq.com 微信登录，复制 SendKey（SCT 开头）\n")
    if not ask_yes("配 Server 酱？", True):
        return {"send_keys": []}
    keys = ask("SendKey（多个逗号分隔）")
    return {"send_keys": [k.strip() for k in keys.split(",") if k.strip()]}


def collect_feishu() -> list:
    print("\n— 飞书自定义机器人（团队场景；可跳过） —")
    if not ask_yes("配飞书 webhook？", False):
        return []
    urls = ask("webhook URL（多个逗号分隔）")
    return [u.strip() for u in urls.split(",") if u.strip()]


def collect_email() -> dict:
    print("\n— 邮件配置（兜底通道，可跳过） —")
    if not ask_yes("现在配邮件？", False):
        return {"email": "", "SMTP": "", "interval_sec": 60}
    print("  QQ 邮箱需要 SMTP 授权码（不是登录密码）：")
    print("  QQ 邮箱 → 设置 → 账户 → POP3/IMAP/SMTP → 开启 SMTP 服务")
    return {
        "email": ask("邮箱地址"),
        "SMTP": ask("SMTP 授权码"),
        "interval_sec": int(ask("最小通知间隔秒", "60") or 60),
    }


def collect_bark() -> list:
    print("\n— Bark 配置（iOS 专用，可跳过） —")
    if not ask_yes("现在配 Bark？", False):
        return []
    keys = ask("Bark key（多个逗号分隔）")
    return [k.strip() for k in keys.split(",") if k.strip()]


def collect_tokens(monitor_list: list) -> dict:
    needs_my = any(s["platform"] == 1 for s in monitor_list)
    needs_pxq = any(s["platform"] == 3 for s in monitor_list)
    print("\n— Token —")
    print("  抓取方法见 ../抓包指南.md\n")
    out = {}
    if needs_my:
        out["my"] = ask("猫眼 token（必填，从微信小程序抓）")
    if needs_pxq:
        out["pxq"] = ask("票星球 token（可选，留空跳过）", "")
    return out


def main():
    if CFG_PATH.exists():
        if not ask_yes(f"{CFG_PATH.name} 已存在，覆盖？", False):
            sys.exit("取消")

    print("======================================")
    print(" TicketRush 监控配置向导")
    print("======================================")

    monitor_list = []
    while True:
        monitor_list.append(add_show(monitor_list))
        if not ask_yes("继续添加演出？", False):
            break

    notice = {
        "telegram": collect_telegram(),
        "serverchan": collect_serverchan(),
        "feishu_webhooks": collect_feishu(),
        "bark_keys": collect_bark(),
    }
    notice.update(collect_email())

    cfg = {
        "proxy": None,
        "token": collect_tokens(monitor_list),
        "monitor_list": monitor_list,
        "notice": notice,
    }

    CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 已写入 {CFG_PATH}")
    print("下一步：python3 start.py")
    print("（启动后会先做自检，token 错误会立刻报出来）")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n取消")
