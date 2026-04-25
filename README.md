# TicketRush

四平台（猫眼 / 大麦 / 纷玩岛 / 票星球）演唱会票务监控 + 半自动抢票工具。

## 这个工具是什么 / 不是什么

✅ **监控四平台库存，回流票出现 1 秒内推 Telegram**
✅ **开抢瞬间在手机端按预设流程自动点 5 步**

❌ **不**自动下单/支付（涉签名+合规风险，刻意不做）
❌ **不**绕过实名 / 滑块 / 人脸

详细战术分析与 SOP 见 [PLAN.md](PLAN.md)。

## 60 秒上手（回流党）

```bash
cd TicketMonitoring-master
pip install -r requirements.txt
python3 setup_wizard.py    # 交互式：粘 URL、填 token、配 Telegram
python3 start.py           # 启动自检 + 心跳 + 自适应监控
```

收到 Telegram 推送 → 立刻打开 App 下单。详见 [PLAN.md §二](PLAN.md)。

## 加挂手机端（首发党）

```bash
# 在 Android 手机的 Termux 内
cd mobile_termux
cp config.json.example config.json    # 改 target_date / target_tickets
termux-wake-lock
python termux_grabber.py
```

详见 [PLAN.md §三](PLAN.md)。

## token 怎么抓

参考 [抓包指南.md](抓包指南.md)。token 是绑你账号的私密凭据，**只能你自己抓**——任何工具帮你抓都意味着拿你的账号。

## 仓库结构

```
TicketRush/
├── README.md / PLAN.md / 抓包指南.md
├── TicketMonitoring-master/    # A 路：监控守护（主力）
│   ├── start.py                # 自检+心跳+自适应频率+Telegram/邮件/Bark
│   ├── setup_wizard.py         # 交互式配置向导
│   ├── telegram_notifier.py
│   ├── email_notifier.py
│   ├── Monitor.py / Monitor_MY/DM/FWD/PXQ.py
│   └── config.json.example
├── mobile_termux/              # B 路：Termux uiautomator2
│   ├── termux_grabber.py
│   ├── config.json.example
│   └── README.md
└── 截图/、周杰伦…猫眼APP界面.jpg  # UI 参考图
```

## 法律合规

- 仅供自用学习，禁止商业代抢
- 不得爬取他人账号数据
- 不得通过本工具绕过平台风控
