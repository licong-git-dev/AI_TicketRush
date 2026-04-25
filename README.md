# TicketRush

四平台（猫眼 / 大麦 / 纷玩岛 / 票星球）演唱会抢票工具，Linux + Android 可用。

## 双路架构

| 路 | 角色 | 实现 | 何时主导 |
|---|---|---|---|
| **A 路** | 官方接口监控 + 通知 | [`TicketMonitoring-master/`](TicketMonitoring-master/) | 全时段（主力） |
| **B 路** | 手机端 UI 自动点击 | [`mobile_termux/`](mobile_termux/) | 开抢瞬间 |

A 路覆盖**首发监控 + 回流票兜底**，B 路覆盖**开抢瞬间点击延迟**。详细打法见 [PLAN.md](PLAN.md)，token 抓取见 [抓包指南.md](抓包指南.md)。

> C 路（Playwright 浏览器 + cookie 复用）PLAN.md 里有描述但**还没实现**——原先的半成品代码里只有硬编码的过期演出 selector，已清理掉。真需要时照 PLAN.md 的 recipe 写 30 行即可。

## 快速上手

```bash
# 主力路：API 监控
cd TicketMonitoring-master
pip install -r requirements.txt
cp config.json.example config.json
# 按 ../抓包指南.md 抓 token 填进去，改 monitor_list 的 show_id
python3 start.py
```

```bash
# 手机端：Termux uiautomator2（Android 手机内执行）
cd mobile_termux
cp config.json.example config.json   # 改 target_date / target_tickets
python termux_grabber.py
```

## 文件结构

```
TicketRush/
├── README.md
├── PLAN.md                   # 抢票战术总纲
├── 抓包指南.md                # 4 平台 token/cookie 抓取
├── TicketMonitoring-master/  # A 路：4 平台 API 监控
├── mobile_termux/            # B 路：Termux uiautomator2
├── 截图/                      # 猫眼票档页参考图
└── 周杰伦演唱会-武汉站-猫眼APP界面.jpg  # 猫眼倒计时弹窗参考图
```

## 法律合规

仅供自用学习。不得爬取他人数据、不得转卖、不得影响平台正常运营。
