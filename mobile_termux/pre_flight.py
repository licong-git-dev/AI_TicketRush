"""
开抢前演练：不抢票，只验证脚本能正确识别当前 App 页面上的元素。

跑：
  python pre_flight.py            # 完整演练
  python pre_flight.py --once     # 只跑一次识别检查

它会：
  1. 检查 config.json 字段
  2. 连 uiautomator2 设备
  3. 拉一次屏幕 hierarchy
  4. 用 config.json 里的 keywords 在 hierarchy 里找匹配，告诉你识别得到几个
  5. 不点击任何按钮（safe）

强烈建议开抢前 1 天跑一遍，免得当天才发现按钮文案变了。
"""

import json
import sys
import time
from pathlib import Path

CFG = Path(__file__).parent / "config.json"


def load() -> dict:
    if not CFG.exists():
        sys.exit(f"❌ {CFG.name} 不存在，先 cp config.json.example config.json")
    return json.loads(CFG.read_text(encoding="utf-8"))


def main():
    cfg = load()

    # 必填字段
    for k in ("target_date", "target_tickets", "keywords"):
        if not cfg.get(k):
            sys.exit(f"❌ config.json 缺字段：{k}")
    if "示例" in cfg["target_date"]:
        sys.exit("❌ target_date 还是示例值，请改成真实场次")

    rate = cfg.get("click_rate_per_sec", 8)
    if rate > 15:
        print(f"⚠️  click_rate_per_sec={rate} 偏高，2025 年起 >15/秒猫眼会封号")

    print("[1/4] 配置字段 ✅")

    try:
        import uiautomator2 as u2
    except ImportError:
        sys.exit("❌ 缺 uiautomator2：pip install uiautomator2")

    print("[2/4] 连接设备…")
    try:
        d = u2.connect()
        info = d.info
        print(f"  ✅ {info.get('productName')} Android {info.get('version')}")
    except Exception as e:
        sys.exit(f"❌ 设备连不上：{e}\n  提示：python -c \"import uiautomator2 as u2; u2.connect().healthcheck()\"")

    print("[3/4] 当前应用…")
    try:
        cur = d.app_current()
        pkg = cur.get("package")
        print(f"  当前 package = {pkg}")
        if pkg not in ("com.sankuai.movie", "cn.damai", "com.taobao.movie.android"):
            print(f"  ⚠️  当前 App 似乎不是猫眼/大麦，识别可能有偏差")
    except Exception as e:
        print(f"  ⚠️  获取当前 App 失败：{e}")

    print("[4/4] 文案识别（从当前页面 dump 找）…")
    try:
        hier = d.dump_hierarchy()
    except Exception as e:
        sys.exit(f"❌ dump_hierarchy 失败：{e}")

    target_date = cfg["target_date"]
    target_tickets = cfg["target_tickets"]
    kws = cfg["keywords"]

    summary = []

    # 场次
    summary.append(("场次", [target_date], target_date in hier))

    # 票档（任一命中即可）
    found_tickets = [t for t in target_tickets if t in hier]
    summary.append(("票档", target_tickets, bool(found_tickets)))

    # 各类按钮
    for label in ("buy", "confirm", "submit", "pay", "refresh", "reservation"):
        words = kws.get(label, [])
        hit = next((w for w in words if w in hier), None)
        summary.append((label, words, hit))

    print("")
    print(f"  {'类别':<12} {'状态':<6} 说明")
    for label, words, hit in summary:
        if hit is True or (isinstance(hit, str) and hit):
            status = "✅"
            note = f"匹配：{hit if isinstance(hit, str) else '是'}"
        else:
            status = "—"
            note = f"未在当前页找到（words={words[:3]}…）"
        print(f"  {label:<12} {status:<6} {note}")

    # 简单建议
    countdown_words = ["天", "时", "分", "秒"]
    has_countdown = any(w in hier for w in countdown_words)
    if has_countdown:
        print("\n💡 当前页有倒计时关键字，时机正确")
    else:
        print("\n💡 当前页没倒计时关键字，可能不是演出详情页")

    print("\n演练完成（未触发任何点击）")


if __name__ == "__main__":
    main()
