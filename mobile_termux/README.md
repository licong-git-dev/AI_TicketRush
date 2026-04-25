# Termux 手机端抢票

在 Android 手机的 Termux 里直接跑 `uiautomator2`，自动点猫眼/大麦 App 的购票流程。无需电脑。

## 一次性安装

```bash
# Termux 从 GitHub/F-Droid 装（不要用 Google Play，版本太旧）
#   https://github.com/termux/termux-app/releases

# Termux 内：
pkg update && pkg upgrade -y
pkg install -y python
pip install uiautomator2

# 开发者选项 → 开启 USB 调试（或 ADB over Wi-Fi）
# 首次初始化 uiautomator2（会自动装 ATX-Agent）
python -c "import uiautomator2 as u2; u2.connect().healthcheck()"
```

## 配置与运行

```bash
cd ~/TicketRush/mobile_termux      # 或脚本所在目录
cp config.json.example config.json
nano config.json                    # 改 target_date 和 target_tickets
python termux_grabber.py
```

`config.json` 三个关键字段：
- `target_date` — 场次文案，必须与 App 里**一字不差**（含空格，如 `"2026-06-15 周六 19:30"`）
- `target_tickets` — 票档优先级数组，从高到低
- `click_rate_per_sec` — 默认 8；**不要超过 15**，猫眼 2025 年起有频率风控

## 后台 + 防休眠

```bash
termux-wake-lock                    # 阻止系统休眠
nohup python termux_grabber.py > grab.log 2>&1 &
tail -f grab.log
pkill -f termux_grabber.py          # 停止
```

还要在系统设置里把 Termux 的**电池优化**关掉，否则息屏几分钟就被杀。

## 排错三板斧

```bash
# 1. 设备能连吗
python -c "import uiautomator2 as u2; print(u2.connect().info)"

# 2. 当前页面能识别到什么（dump 前 5000 字）
python -c "import uiautomator2 as u2; print(u2.connect().dump_hierarchy()[:5000])"

# 3. 直接点特定文案验证
python -c "import uiautomator2 as u2; u2.connect()(text='立即预订').click()"
```

日志写在 `/sdcard/抢票日志_<时间戳>.txt`。

## 已知局限

- 息屏 + 电池优化没关 → uiautomator2 被系统冻结，失效。
- App 改版导致按钮文案变化 → 去 `config.json.example` 的 `keywords` 节里补一行。
- 连击频率 >20/秒 → 触发风控封号，不要手欠调大。
