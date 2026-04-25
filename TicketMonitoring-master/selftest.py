"""
自检命令：跑一遍 config.json 是否完整、token 是否有效、通知通道是否可达。
不做任何抢票/下单。出错直接退码非零，方便接 systemd / cron 监控。

用法：
  python3 selftest.py            # 完整自检
  python3 selftest.py --quiet    # 只打错误
"""

import json
import sys
from datetime import datetime
from pathlib import Path


CFG = Path(__file__).parent / "config.json"


def load_cfg() -> dict:
    if not CFG.exists():
        sys.exit(f"❌ {CFG.name} 不存在；先运行 setup_wizard.py")
    with CFG.open(encoding="utf-8") as f:
        return json.load(f)


def check_structure(cfg: dict) -> list:
    errs = []
    if not cfg.get("monitor_list"):
        errs.append("monitor_list 为空")
    for s in cfg.get("monitor_list", []):
        for k in ("show_id", "show_name", "platform", "deadline"):
            if k not in s or s[k] == "":
                errs.append(f"演出 {s.get('show_name', '?')} 缺字段 {k}")
        try:
            dt = datetime.strptime(s.get("deadline", ""), "%Y-%m-%d %H:%M:%S")
            if dt < datetime.now():
                errs.append(f"演出 {s.get('show_name')} deadline 已过 ({s['deadline']})")
        except ValueError:
            errs.append(f"演出 {s.get('show_name')} deadline 格式错误，应为 YYYY-MM-DD HH:MM:SS")
    if "示例" in str(cfg.get("monitor_list", [])):
        errs.append("monitor_list 还是示例值，请改成真实 show_id")
    return errs


def check_token(cfg: dict) -> list:
    errs = []
    plats = {s.get("platform") for s in cfg.get("monitor_list", [])}
    token = cfg.get("token", {}) or {}
    if 1 in plats and not token.get("my"):
        errs.append("有猫眼监控但 token.my 为空")
    if 3 in plats and not token.get("pxq"):
        errs.append("票星球可不需要 token，跳过此项")  # 信息性，不阻塞
    return errs


def check_channels(cfg: dict, quiet: bool) -> list:
    notice = cfg.get("notice", {}) or {}
    active = []

    tg = notice.get("telegram", {}) or {}
    if tg.get("bot_token") and tg.get("chat_ids"):
        try:
            from telegram_notifier import TelegramNotifier
            n = TelegramNotifier()
            err = n.healthcheck()
            if err:
                print(f"  ⚠️  Telegram: {err}")
            else:
                if not quiet:
                    print("  ✅ Telegram bot 可达")
                active.append("Telegram")
        except Exception as e:
            print(f"  ⚠️  Telegram 检查异常: {e}")

    sc = notice.get("serverchan", {}) or {}
    if sc.get("send_keys"):
        active.append("Server 酱")
        if not quiet:
            print("  ✅ Server 酱已配置 (key 数量 {})".format(len(sc["send_keys"])))

    if notice.get("feishu_webhooks"):
        active.append("飞书")
        if not quiet:
            print("  ✅ 飞书已配置 ({})".format(len(notice["feishu_webhooks"])))

    if notice.get("email") and notice.get("SMTP"):
        active.append("邮件")
        if not quiet:
            print("  ✅ 邮件已配置")

    if notice.get("bark_keys"):
        active.append("Bark")
        if not quiet:
            print("  ✅ Bark 已配置")

    if not active:
        return ["没有任何通知通道，回流告警将丢失"]
    return []


def check_monitors(cfg: dict, quiet: bool) -> list:
    """实例化每个 Monitor，跑一次 monitor() 验证 token/show_id 真有效"""
    errs = []
    sys.path.insert(0, str(Path(__file__).parent))
    PLATFORMS = {0: "大麦", 1: "猫眼", 2: "纷玩岛", 3: "票星球"}
    for show in cfg.get("monitor_list", []):
        plat = show.get("platform")
        name = PLATFORMS.get(plat, f"平台{plat}")
        try:
            if plat == 0:
                from Monitor_DM import DM as Cls
            elif plat == 1:
                from Monitor_MY import MY as Cls
            elif plat == 2:
                from Monitor_FWD import FWD as Cls
            elif plat == 3:
                from Monitor_PXQ import PXQ as Cls
            else:
                errs.append(f"{show.get('show_name')} 未知 platform={plat}")
                continue
            m = Cls(show)
            res = m.monitor()
            if not quiet:
                print(f"  ✅ {name} {show.get('show_name')} 自检 OK，当前可买 {len(res)} 档")
        except Exception as e:
            errs.append(f"{name} {show.get('show_name')} 自检失败：{str(e)[:200]}")
    return errs


def main():
    quiet = "--quiet" in sys.argv
    print("🔍 TicketRush 自检")
    print("=" * 50)

    cfg = load_cfg()

    all_errs = []

    if not quiet:
        print("\n[1/4] 配置结构…")
    errs = check_structure(cfg)
    all_errs += errs
    for e in errs:
        print(f"  ❌ {e}")

    if not quiet:
        print("\n[2/4] Token 字段…")
    errs = [e for e in check_token(cfg) if "可不需要" not in e]
    all_errs += errs
    for e in errs:
        print(f"  ❌ {e}")

    if not quiet:
        print("\n[3/4] 通知通道…")
    errs = check_channels(cfg, quiet)
    all_errs += errs
    for e in errs:
        print(f"  ❌ {e}")

    if not quiet:
        print("\n[4/4] 真实接口（每个监控对象跑一次 monitor()）…")
    errs = check_monitors(cfg, quiet)
    all_errs += errs
    for e in errs:
        print(f"  ❌ {e}")

    print("=" * 50)
    if all_errs:
        print(f"⛔ 自检失败 {len(all_errs)} 项")
        sys.exit(1)
    print("🎉 全部通过，可以 python3 start.py 启动监控")


if __name__ == "__main__":
    main()
