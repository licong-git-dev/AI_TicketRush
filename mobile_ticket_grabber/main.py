from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException
import time

# 导入所有配置
from config import (
    APPIUM_SERVER_URL,
    DEVICE_NAME,
    APP_PACKAGE,
    APP_ACTIVITY,
    TARGET_DATE_TEXT,
    TARGET_TICKET_TEXT,
    INITIAL_BUTTON_KEYWORDS,
    SELECTION_CONFIRM_KEYWORDS,
    ORDER_CONFIRM_KEYWORDS,
    PAYMENT_KEYWORDS,
    REFRESH_KEYWORDS,
    RESERVATION_KEYWORDS,
    COUNTDOWN_KEYWORDS
)

def find_element_by_keywords(driver, keywords, exact_match=False):
    """查找元素但不点击，返回找到的元素或None"""
    for keyword in keywords:
        try:
            xpath = f"//*[@text='{keyword}']" if exact_match else f"//*[contains(@text, '{keyword}')]"
            elements = driver.find_elements(AppiumBy.XPATH, xpath)
            for elem in elements:
                if elem and elem.is_displayed():
                    return elem
        except Exception:
            continue
    return None

def find_and_click(driver, keywords, description, timeout=10, exact_match=False, high_speed_click=False, silent=False):
    """
    通用查找并点击函数 v4.0
    - 支持关键字模糊匹配和文本精确匹配
    - 集成智能刷新机制
    - 支持高速点击模式
    - 支持静默模式，抑制日志输出
    - 增强错误恢复能力
    """
    if not silent:
        print(f"\n--- {description} ---")

    start_time = time.time()
    last_refresh_time = 0

    while time.time() - start_time < timeout:
        # 查找目标元素
        button = find_element_by_keywords(driver, keywords, exact_match)

        if button:
            if not silent:
                print(f"成功找到目标: '{button.text}'")

            try:
                if high_speed_click:
                    if not silent:
                        print("进入高速点击模式...")
                    click_count = 0
                    while click_count < 50:  # 最多点击50次
                        try:
                            button.click()
                            click_count += 1
                            time.sleep(0.05)  # 20次/秒
                        except Exception:
                            if not silent:
                                print(f"高速点击{click_count}次后页面跳转")
                            return True
                    return True
                else:
                    button.click()
                    if not silent:
                        print("点击成功。")
                    return True
            except Exception as e:
                if not silent:
                    print(f"点击失败，尝试重新查找: {e}")
                time.sleep(0.3)
                continue

        # 如果找不到目标，尝试刷新（每3秒最多刷新一次）
        current_time = time.time()
        if not silent and current_time - last_refresh_time > 3:
            refresh_button = find_element_by_keywords(driver, REFRESH_KEYWORDS)
            if refresh_button:
                print(f"找到刷新按钮，正在刷新...")
                try:
                    refresh_button.click()
                    last_refresh_time = current_time
                    time.sleep(1)
                    continue
                except Exception:
                    pass

        time.sleep(0.2)

    if not silent:
        print(f"超时: 在 {timeout} 秒内未找到 '{description}'")
    return False

def check_countdown_status(driver):
    """检查是否存在倒计时，返回倒计时信息"""
    try:
        # 查找倒计时元素
        for keyword in COUNTDOWN_KEYWORDS:
            elements = driver.find_elements(AppiumBy.XPATH, f"//*[contains(@text, '{keyword}')]")
            if elements:
                countdown_text = " ".join([elem.text for elem in elements if elem.is_displayed()])
                return countdown_text
    except Exception:
        pass
    return None

def check_reservation_status(driver):
    """检查是否已预约"""
    try:
        for keyword in RESERVATION_KEYWORDS:
            elements = driver.find_elements(AppiumBy.XPATH, f"//*[contains(@text, '{keyword}')]")
            if elements and any(elem.is_displayed() for elem in elements):
                return True
    except Exception:
        pass
    return False

def main():
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.udid = '127.0.0.1:16384'  # 强制连接到指定设备
    options.device_name = DEVICE_NAME
    options.app_package = APP_PACKAGE
    options.app_activity = APP_ACTIVITY
    options.no_reset = True
    options.automation_name = 'UiAutomator2'
    options.new_command_timeout = 600

    driver = None
    try:
        driver = webdriver.Remote(APPIUM_SERVER_URL, options=options)
        print("Appium WebDriver 初始化成功。")
        print("智能抢票脚本 v3.0 已启动，将自动识别当前页面并执行操作。")
        print("请将App切换到前台，脚本将自动处理后续流程。")

        last_action_time = time.time()
        max_inactivity_seconds = 300  # 5分钟无操作才退出，给予充足时间

        print("\n🤖 智能抢票引擎已启动")
        print("📱 请确保猫眼App在前台")
        print("⏰ 系统将持续监控页面并自动执行操作\n")

        while time.time() - last_action_time < max_inactivity_seconds:
            action_taken = False

            # 优先检查倒计时和预约状态
            countdown = check_countdown_status(driver)
            is_reserved = check_reservation_status(driver)

            if countdown:
                elapsed = int(time.time() - last_action_time)
                print(f"⏰ 倒计时: {countdown} | 已等待: {elapsed}秒")
                if is_reserved:
                    print("✅ 已预约，持续监控等待开抢...")
                    time.sleep(2)
                    last_action_time = time.time()  # 重置计时器
                    action_taken = True
                    continue
                else:
                    print("🔄 尚未预约，尝试点击预约...")

            # 倒序检查，从流程的最后一步开始，确保状态判断的准确性
            # 步骤 5: 支付
            if find_and_click(driver, PAYMENT_KEYWORDS, "支付", timeout=1, silent=True):
                print("💳 检测到支付页面，尝试点击支付...")
                find_and_click(driver, PAYMENT_KEYWORDS, "确认支付", timeout=5)
                print("✅ 支付流程已尝试，脚本任务完成。")
                action_taken = True
                break # 支付后直接退出循环

            # 步骤 4: 提交订单
            elif find_and_click(driver, ORDER_CONFIRM_KEYWORDS, "提交订单", timeout=1, silent=True, high_speed_click=True):
                print("🚀 检测到提交订单页面，高速点击提交...")
                action_taken = True

            # 步骤 3: 确认选择
            elif find_and_click(driver, SELECTION_CONFIRM_KEYWORDS, "确认选择", timeout=1, silent=True):
                print("✔️ 检测到票档/座位确认按钮，点击确认...")
                action_taken = True

            # 步骤 2: 选择票档
            elif find_and_click(driver, TARGET_TICKET_TEXT, "选择目标票档", exact_match=True, timeout=1, silent=True):
                print(f"🎫 检测到票档选择页面，尝试选择: {TARGET_TICKET_TEXT[0]}")
                action_taken = True

            # 步骤 1: 选择场次
            elif find_and_click(driver, TARGET_DATE_TEXT, "选择目标场次", exact_match=True, timeout=1, silent=True):
                print(f"📅 检测到场次选择页面，尝试选择: {TARGET_DATE_TEXT[0]}")
                action_taken = True

            # 步骤 0: 初始购买
            elif find_and_click(driver, INITIAL_BUTTON_KEYWORDS, "初始购买按钮", timeout=1, silent=True):
                print("🛒 检测到演出详情页，点击购买按钮...")
                action_taken = True

            if action_taken:
                last_action_time = time.time()  # 重置无操作计时器
                time.sleep(0.5)  # 短暂等待页面刷新
            else:
                elapsed = int(time.time() - last_action_time)
                if not countdown:
                    if elapsed % 10 == 0:  # 每10秒提示一次，减少刷屏
                        print(f"⏳ 等待可识别操作... ({elapsed}秒)")
                time.sleep(1)
        
        if time.time() - last_action_time >= max_inactivity_seconds:
            print(f"\n⚠️  {max_inactivity_seconds}秒内无可识别操作，脚本终止")
            print("\n可能原因：")
            print("1. ❌ 无障碍服务未开启（最常见！）")
            print("   → 手机【设置】->【无障碍】->开启UiAutomator2")
            print("2. ❌ App未在抢票相关页面")
            print("   → 请打开猫眼App到演出详情页")
            print("3. ❌ 关键字配置不匹配")
            print("   → 检查config.py中的按钮文字")
            print("\n💡 建议: 运行【诊断Appium连接.py】检查配置")

    except Exception as e:
        print(f"\n发生严重错误: {e}")
        print("抢票流程意外终止。")
    finally:
        if driver:
            print("脚本执行完毕，5秒后自动关闭连接。")
            time.sleep(5)
            driver.quit()

if __name__ == '__main__':
    main()