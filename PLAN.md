# 抢票实战计划（务实版）

> 编写日期：2026-04-25
> 仓库目标：在猫眼/大麦/纷玩岛/票星球四大平台**真正抢到票**，而不是写一堆跑不起来的脚本。

---

## 一、先想清楚：为什么之前不一定能抢到

抢票成败由 4 个环节决定，缺一不可：

1. **账号侧**：实名 + 收货地址 + 免密支付 + 提前预约/收藏 → 这一步决定你有没有资格点。
2. **网络侧**：与售票服务器物理距离、运营商出口、HTTPS 握手时间 → 决定你的请求第几个到。
3. **接口侧 vs UI 侧**：直接打官方 HTTP 接口比 UI 自动化快 5–50 倍。**但接口需要登录态/签名**，平台风控也最严。
4. **执行侧**：脚本响应延迟、点击节奏、风控规避。

之前仓库的所有方案几乎只解决了"4 执行侧"。这次必须把 1–3 都补齐。

---

## 二、两路并发 + 回流兜底

| 路 | 角色 | 何时主导 | 实现 |
|---|---|---|---|
| **A. API 监控 + 通知** | 主力，接口层轮询库存 | 全时段 | `TicketMonitoring-master/` |
| **B. 手机 UI 自动化** | 开抢瞬间的点击延迟最低 | 开抢 T±60s | `mobile_termux/` |
| **C. 浏览器 + Cookie 复用** | 可选；真要做需自己写 | 按需 | 未实现，见三-C 推荐写法 |
| **D. 回流票监控** | 没抢到时持续守候 | 开抢后–开演前 | 复用 A 路 |

**关键认知**：A 路门槛在抓 token（一次性），但能 7×24 跑；B 路门槛低但只能在开抢那一刻发挥作用。两路并用命中率最高。

---

## 三、各路具体怎么做

### A. API 直连（最高优先级）

`TicketMonitoring-master/` 里已有 4 个平台的**列表查询**接口（猫眼 `Monitor_MY.py`、大麦 `Monitor_DM.py`、纷玩岛 `Monitor_FWD.py`、票星球 `Monitor_PXQ.py`）。但当前代码**只能监控有没有票，不能直接下单**。

要做的事：
1. **抓包目标**（按优先级）：
   - 猫眼小程序 `wx.maoyan.com/my/odea/...` 创建订单接口（`createOrder` / `submitOrder`）
   - 大麦 `mtop.damai.trade.order.build/create` 系列
   - 工具：手机装 Stream/小黄鸟（Android）或 Charles + 微信小程序代理。
2. **拿 3 个东西**：`token` / `cookie` / `User-Agent`（与 `Monitor_MY.py:74-83` 已有的 headers 拼装方式一致）。
3. **新增模块** `auto_buyer/`（仓库还没建）：
   - `buyer_my.py` —— 在 `Monitor_MY.monitor()` 检测到 `remainingStock` 时，立即 `requests.post(下单URL, headers=headers, json=payload)`。
   - 复用 `email_notifier.py` 做成功通知。
4. **风险**：猫眼/大麦的下单接口都有 `mtop-sign` / `sing` 签名。如果签名算法没逆向出来，A 路退化成只能监控、人手补刀点击。

**最低可用版（MVP）：先跑监控，抢到票时邮件 + Bark 推送，人手 30 秒内确认下单。** 这一步不需要破签名，今天就能跑。

### B. 手机端 Termux + uiautomator2

`mobile_termux/termux_grabber.py` 已经能用，问题：
- 配置里 `TARGET_DATE = "2025-09-27 周六 19:30"` **早过期**，必须改。
- 50 次/秒的疯狂点击在猫眼当前风控下**很可能触发限流**（2025 年下半年起猫眼加强了点击频率检测）。建议改成：开抢前 200ms 起每秒 5–8 次，上限 15 次。
- 锁屏后 uiautomator2 不工作 → 必须 `termux-wake-lock` + 关闭电池优化 + 屏幕常亮。

部署步骤：
```bash
# 手机 Termux 内
pkg update && pkg install python tsu
pip install uiautomator2
# 把脚本 push 进去（adb push 或微信传文件）
python -m uiautomator2 init   # 第一次需要在被控手机上确认
python termux_grabber.py
```

### C. 浏览器 Cookie 复用（未实现，需自写）

原仓库里有过 `pc_ticket_grabber/` + `backend/` 两份 Playwright 半成品，已清理掉——它们都没做 cookie 持久化，而且 selector 绑死在已过期的周杰伦武汉站。如果你真要上 C 路，写新的，30 行足够：

```python
# 第一次运行：手动扫码登录，保存登录态
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    ctx = p.chromium.launch(headless=False).new_context()
    page = ctx.new_page()
    page.goto("https://passport.maoyan.com/pc/login")
    input("扫码登录完成后回车…")
    ctx.storage_state(path="auth.json")

# 抢票时：复用登录态
ctx = p.chromium.launch(headless=False).new_context(storage_state="auth.json")
# 开抢前 5 秒预热到选座/票档页，倒计时结束瞬间点提交
```

`auth.json` 已在 `.gitignore` 里，不会误提交。

### D. 回流票（最重要的兜底）

99% 的人抢首发会失败。**真正能拿到票的更多是回流。** `TicketMonitoring-master/start.py` 默认 1 秒轮询一次：
```bash
cd TicketMonitoring-master
pip install -r requirements.txt
# 编辑 config.json：填 token、show_id、deadline、邮箱 SMTP
python3 start.py
```
建议：
- 部署到一台 7×24 小时的小服务器（阿里云 99 元/年那种），不要放在你电脑上。
- `interval_sec` 从 300 调到 60（每分钟最多一封邮件）。
- 把 Bark 通知（`Monitor.py:31`）启用——iPhone 推送 < 1 秒。

---

## 四、开抢前 24 小时清单

- [ ] 目标场次的 `show_id` 在 4 个平台都查出来 → 写入 `TicketMonitoring-master/config.json`
- [ ] 4 个平台 App 都登录 + 实名 + 绑定收货地址 + 开通免密支付
- [ ] 目标演出在每个平台都点了"想看"/"预约"/"提醒"
- [ ] Termux 脚本里 `TARGET_DATE` / `TARGET_TICKETS` 改成新场次
- [ ] 手机：电池 100%、关省电、屏幕常亮、流量+WiFi 双备
- [ ] 在抢票前一天**完整跑一次彩排**（用一个低热度演出试下单到付款页 → 关掉）
- [ ] NTP 校时：`sudo ntpdate ntp.aliyun.com`（电脑端），手机打开"自动设置时间"
- [ ] 备一个家人/朋友的账号同时蹲

---

## 五、开抢瞬间剧本（T-60s 起）

| 时刻 | 动作 |
|---|---|
| T-60s | 三路全部启动并停在选座/票档页 |
| T-30s | 手机端 `python 周杰伦…_termux_grabber.py` 开始监听 |
| T-10s | 浏览器 F5 一次确认会话有效 |
| T-1s | 不要再点刷新（容易把会话刷掉） |
| T+0 | A 路打接口 / B 路点立即购买 / C 路人手点 |
| T+30s | 任何一路成功 → 立刻支付（5–10 分钟订单超时） |
| T+5min | 都没成功 → 切换到 D 路监控，准备守 7 天回流 |

---

## 六、最容易踩的坑

1. **疯狂点击触发风控**：50 次/秒已经是 2023 年的打法，2025 起平台普遍封号。
2. **没绑支付方式**：抢到了 5 分钟付不掉照样飞。
3. **同一 IP 多账号**：会被关联封号。家庭路由器 + 手机 4G + 朋友家 = 3 个独立 IP。
4. **token 过期**：猫眼小程序 token 一般 30 天有效，开抢前 1 天必须重新抓。
5. **签名算法**：大麦的 `sing`、猫眼的 `mt-token` 都是混淆 JS 算的，没破出来就别幻想全自动下单——老老实实用 B+C 半自动。

---

## 七、当前仓库结构

```
TicketRush/
├── README.md                 # 项目说明
├── PLAN.md                   # ← 你现在看的这份
├── 抓包指南.md                # 4 平台 token/cookie 抓取
├── TicketMonitoring-master/  # 【A 路 · 主力】4 平台 API 监控
├── mobile_termux/            # 【B 路】手机端 uiautomator2
├── 截图/                      # 猫眼票档页参考图
└── 周杰伦演唱会-武汉站-猫眼APP界面.jpg  # 猫眼倒计时弹窗参考图
```

---

## 八、立刻可做的下一步（按顺序）

1. **告诉我目标演出**（演员、城市、日期）→ 我帮你查 4 个平台的 `show_id` 并把 `config.json` 写好。
2. 装 `TicketMonitoring-master/`，先把回流监控跑起来——这是兜底，越早越好。
3. 抓一次猫眼小程序的 token，验证监控能拿到真实库存数据。
4. 等抓包拿到下单接口后，再决定 A 路是做"自动下单"还是"快速通知 + 人手"。
