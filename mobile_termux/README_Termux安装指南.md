# 📱 Termux版智能抢票 - 完整安装指南

## 🎯 优势特点

✅ **直接在手机运行** - 无需电脑，无需数据线
✅ **后台持续运行** - 支持息屏运行，不影响使用手机
✅ **功能最强大** - 完整Python功能，智能识别
✅ **安装简单** - 10分钟搞定，一次配置永久使用
✅ **完全免费** - 开源方案，无需付费

---

## 📋 安装步骤

### 第1步：安装Termux

**下载安装：**
- 方法1：GitHub下载 [推荐]
  ```
  https://github.com/termux/termux-app/releases
  下载最新的 termux-app_vX.X.X+github-debug_arm64-v8a.apk
  ```

- 方法2：F-Droid下载
  ```
  https://f-droid.org/en/packages/com.termux/
  ```

⚠️ **注意：不要从Google Play下载，版本太旧！**

### 第2步：基础环境配置

打开Termux，依次运行：

```bash
# 更新软件源
pkg update && pkg upgrade

# 安装Python和依赖
pkg install python

# 安装自动化库
pip install uiautomator2

# 安装辅助工具
pkg install wget curl git

# 创建工作目录
mkdir ~/ticket_grabber
cd ~/ticket_grabber
```

### 第3步：下载抢票脚本

```bash
# 下载脚本（替换为实际下载链接）
wget -O termux_grabber.py "脚本下载链接"

# 或者手动创建文件
nano termux_grabber.py
# 粘贴脚本内容，Ctrl+X保存
```

### 第4步：开启开发者选项

**在手机设置中：**
1. 打开【设置】→【关于手机】
2. 连续点击【版本号】7次
3. 返回【设置】，找到【开发者选项】
4. 开启【USB调试】
5. 开启【USB调试（安全设置）】

### 第5步：初始化UiAutomator2

**在Termux中运行：**
```bash
python -c "import uiautomator2 as u2; print(u2.connect().info)"
```

**首次运行会自动：**
- 安装ATX-Agent
- 安装UiAutomator2-APK
- 配置必要权限

⚠️ **如果失败，手动安装：**
```bash
python -c "import uiautomator2 as u2; u2.connect().healthcheck()"
```

---

## 🚀 使用方法

### 配置抢票参数

编辑脚本：
```bash
nano termux_grabber.py
```

修改配置区域：
```python
# 目标场次
TARGET_DATE = "2025-09-27 周六 19:30"

# 目标票档 (按优先级排序)
TARGET_TICKETS = [
    "内场至尊VIP ¥2000",
    "内场VIP ¥1800",
    "内场 ¥1600",
    "看台 ¥1300",
    "看台 ¥1000",
    "看台 ¥800",
    "看台 ¥600"
]
```

### 运行抢票

```bash
# 启动抢票程序
python termux_grabber.py
```

### 后台运行

```bash
# 后台运行（推荐）
nohup python termux_grabber.py > grab.log 2>&1 &

# 查看运行状态
ps aux | grep python

# 查看日志
tail -f grab.log

# 停止程序
pkill -f termux_grabber.py
```

---

## 🔧 高级技巧

### 自动启动

**创建启动脚本：**
```bash
nano ~/start_grabber.sh
```

**内容：**
```bash
#!/bin/bash
cd ~/ticket_grabber
echo "🎫 启动智能抢票..."
python termux_grabber.py
```

**设置可执行：**
```bash
chmod +x ~/start_grabber.sh
```

**使用：**
```bash
~/start_grabber.sh
```

### 定时启动

**安装cron：**
```bash
pkg install cronie
```

**编辑定时任务：**
```bash
crontab -e
```

**添加任务（例如每天19:25启动）：**
```
25 19 * * * cd ~/ticket_grabber && python termux_grabber.py
```

### 电量优化

**防止休眠：**
```bash
# 获取唤醒锁
termux-wake-lock

# 释放唤醒锁
termux-wake-unlock
```

**省电模式设置：**
- 设置 → 电池 → 省电模式 → 关闭
- 设置 → 应用管理 → Termux → 电池优化 → 不优化

---

## 🛠️ 故障排查

### 问题1: "找不到设备"

**解决方案：**
```bash
# 检查UiAutomator2状态
python -c "import uiautomator2 as u2; print(u2.connect().info)"

# 重新初始化
python -c "import uiautomator2 as u2; u2.connect().healthcheck()"
```

### 问题2: "权限不足"

**解决方案：**
1. 确认开发者选项已开启
2. 确认USB调试已开启
3. 重启手机后重新运行

### 问题3: "模块找不到"

**解决方案：**
```bash
# 重新安装
pip install --upgrade uiautomator2

# 或者使用国内源
pip install -i https://pypi.douban.com/simple/ uiautomator2
```

### 问题4: "脚本无反应"

**解决方案：**
1. 检查是否在猫眼App页面
2. 确认配置的关键字与App界面一致
3. 查看日志文件：`tail -f /sdcard/抢票日志_*.txt`

---

## 📱 完整操作流程

### 抢票前准备
1. ✅ 按上述步骤安装Termux和脚本
2. ✅ 配置目标场次和票档
3. ✅ 开启开发者选项和USB调试
4. ✅ 手机充好电并连接充电器

### 抢票时操作
1. **提前运行脚本**
   ```bash
   python termux_grabber.py
   ```

2. **切换到猫眼App**
   - 打开猫眼到演出详情页
   - 可以看到倒计时

3. **观察自动操作**
   - 脚本会自动监控页面变化
   - 倒计时结束时自动开抢
   - 实时日志显示操作状态

4. **等待完成**
   - 抢票成功会显示"🎉 抢票成功！"
   - 到达支付页面需手动完成支付

---

## 💡 使用技巧

### 提高成功率
1. **提前预约**：如果演出支持预约，提前预约
2. **网络优化**：使用5G或高速WiFi
3. **多档备选**：配置多个票档作为备选
4. **提前启动**：提前5-10分钟运行脚本

### 调试技巧
1. **查看页面元素**：
   ```bash
   python -c "import uiautomator2 as u2; print(u2.connect().dump_hierarchy())"
   ```

2. **截图调试**：
   ```bash
   python -c "import uiautomator2 as u2; u2.connect().screenshot('debug.png')"
   ```

3. **测试点击**：
   ```bash
   python -c "import uiautomator2 as u2; u2.connect()(text='立即购买').click()"
   ```

---

## 🆚 方案对比

| 方案 | 优势 | 劣势 | 推荐度 |
|------|------|------|-------|
| **Termux版** | 功能最强，后台运行，无需电脑 | 需要一次配置 | ⭐⭐⭐⭐⭐ |
| Android APP版 | 界面友好，一键启动 | 需要编译APK | ⭐⭐⭐⭐ |
| Tasker版 | 安装简单，轻量级 | 功能有限 | ⭐⭐⭐ |
| 电脑+Appium版 | 调试方便，日志详细 | 需要数据线连接 | ⭐⭐ |

---

## 🎯 总结

**Termux版本是最推荐的方案！**

✅ **一次配置，永久使用**
✅ **手机独立运行，无需电脑**
✅ **后台运行不影响手机使用**
✅ **功能强大，识别准确**

**10分钟安装，轻松抢票！** 🎉

---

## 📞 技术支持

遇到问题？

1. **查看日志**：`tail -f /sdcard/抢票日志_*.txt`
2. **检查环境**：`python -c "import uiautomator2; print('OK')"`
3. **重新初始化**：`python -c "import uiautomator2 as u2; u2.connect().healthcheck()"`

**开始你的抢票之旅吧！** 🚀