# TicketRush

四平台（猫眼 / 大麦 / 纷玩岛 / 票星球）演唱会抢票工具集，Linux/手机端可用。

## 实战路线

详细步骤见 [PLAN.md](./PLAN.md)。一句话总结：

- **A 路（主力）**：API 监控 + 自动下单 → `TicketMonitoring-master/`
- **B 路（备份）**：手机 Termux + uiautomator2 → `mobile_termux/`
- **C 路（兜底）**：Playwright 浏览器复用 cookie → `pc_ticket_grabber/`、`backend/`
- **D 路（回流）**：长期守候退票回流 → 复用 A 路监控

## 模块说明

| 目录 | 用途 | 状态 |
|---|---|---|
| `TicketMonitoring-master/` | 4 平台官方接口轮询，能监控+邮件/Bark 通知 | 开箱即用，需填 `config.json` |
| `mobile_termux/` | 手机端 uiautomator2 自动点击猫眼 App | 配置里日期已过期，需更新 `TARGET_DATE` |
| `mobile_ticket_grabber/` | Appium（电脑控制手机）版，与 termux 同逻辑 | 备选方案，不推荐 |
| `pc_ticket_grabber/` | Playwright 浏览器自动化（猫眼 PC 端） | 半成品，需改 cookie 复用 |
| `backend/` | FastAPI 骨架，给 C 路做 Web 控制台 | 仅脚手架 |
| `截图/` | 界面参考图，调按钮关键字时对照 | 资料 |

## 快速开始

```bash
# 主力路：API 监控
cd TicketMonitoring-master
pip install -r requirements.txt
# 编辑 config.json，填入 token / show_id / 邮件 SMTP
python3 start.py
```

## 法律合规

仅供学习研究使用，禁止商业化。请遵守各平台用户协议。
