#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版抢票脚本 v5.0
- 全面的界面识别能力
- 智能异常恢复
- 详细的操作日志
- 支持倒计时自动开抢
"""

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import time
import re

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

class SmartTicketGrabber:
    def __init__(self):
        self.driver = None
        self.last_action_time = time.time()
        self.action_log = []

    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.action_log.append(log_entry)

    def find_elements_safe(self, keywords, exact_match=False):
        """安全地查找元素，返回所有匹配的可见元素"""
        found_elements = []
        for keyword in keywords:
            try:
                xpath = f"//*[@text='{keyword}']" if exact_match else f"//*[contains(@text, '{keyword}')]"
                elements = self.driver.find_elements(AppiumBy.XPATH, xpath)
                for elem in elements:
                    try:
                        if elem and elem.is_displayed():
                            found_elements.append((keyword, elem))
                    except StaleElementReferenceException:
                        continue
            except Exception as e:
                continue
        return found_elements

    def click_element_safe(self, element, description):
        """安全地点击元素，带重试机制"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                element.click()
                self.log(f"✅ {description} - 点击成功", "SUCCESS")
                return True
            except StaleElementReferenceException:
                self.log(f"⚠️ {description} - 元素过期，重试 {attempt+1}/{max_retries}", "WARN")
                time.sleep(0.3)
                continue
            except Exception as e:
                self.log(f"❌ {description} - 点击失败: {e}", "ERROR")
                return False
        return False

    def check_countdown(self):
        """检查倒计时状态"""
        try:
            page_source = self.driver.page_source
            # 匹配倒计时格式: XX天XX时XX分XX秒
            countdown_pattern = r'(\d+天|\d+时|\d+分|\d+秒)'
            matches = re.findall(countdown_pattern, page_source)
            if matches:
                countdown_str = " ".join(matches[:4])  # 最多取4个部分
                return countdown_str
        except Exception:
            pass
        return None

    def check_reservation(self):
        """检查是否已预约"""
        elements = self.find_elements_safe(RESERVATION_KEYWORDS)
        return len(elements) > 0

    def smart_refresh(self):
        """智能刷新页面"""
        refresh_elements = self.find_elements_safe(REFRESH_KEYWORDS)
        if refresh_elements:
            keyword, elem = refresh_elements[0]
            if self.click_element_safe(elem, f"刷新按钮({keyword})"):
                time.sleep(1)
                return True
        return False

    def handle_initial_page(self):
        """处理初始购买页面"""
        elements = self.find_elements_safe(INITIAL_BUTTON_KEYWORDS)
        if elements:
            keyword, elem = elements[0]
            self.log(f"🛒 检测到购买按钮: {keyword}")
            if self.click_element_safe(elem, f"购买按钮({keyword})"):
                self.last_action_time = time.time()
                return True
        return False

    def handle_date_selection(self):
        """处理场次选择"""
        elements = self.find_elements_safe(TARGET_DATE_TEXT, exact_match=True)
        if elements:
            keyword, elem = elements[0]
            self.log(f"📅 检测到目标场次: {keyword}")
            if self.click_element_safe(elem, f"场次({keyword})"):
                self.last_action_time = time.time()
                return True
        return False

    def handle_ticket_selection(self):
        """处理票档选择（多档位优先级）"""
        for ticket_text in TARGET_TICKET_TEXT:
            elements = self.find_elements_safe([ticket_text], exact_match=True)
            if elements:
                keyword, elem = elements[0]
                self.log(f"🎫 检测到票档: {keyword}")
                if self.click_element_safe(elem, f"票档({keyword})"):
                    self.last_action_time = time.time()
                    return True
        return False

    def handle_confirm_selection(self):
        """处理确认选择"""
        elements = self.find_elements_safe(SELECTION_CONFIRM_KEYWORDS)
        if elements:
            keyword, elem = elements[0]
            self.log(f"✔️ 检测到确认按钮: {keyword}")
            if self.click_element_safe(elem, f"确认({keyword})"):
                self.last_action_time = time.time()
                return True
        return False

    def handle_order_submit(self):
        """处理订单提交（高速点击）"""
        elements = self.find_elements_safe(ORDER_CONFIRM_KEYWORDS)
        if elements:
            keyword, elem = elements[0]
            self.log(f"🚀 检测到提交订单按钮: {keyword}")
            self.log("⚡ 启动高速点击模式...", "INFO")

            click_count = 0
            max_clicks = 50
            start_time = time.time()

            while click_count < max_clicks:
                try:
                    elem.click()
                    click_count += 1
                    time.sleep(0.03)  # 33次/秒
                except StaleElementReferenceException:
                    # 元素过期说明页面跳转了，停止点击
                    break
                except Exception as e:
                    break

            elapsed = time.time() - start_time
            self.log(f"⚡ 高速点击完成: {click_count}次点击 / {elapsed:.2f}秒", "SUCCESS")
            self.last_action_time = time.time()
            return True
        return False

    def handle_payment(self):
        """处理支付"""
        elements = self.find_elements_safe(PAYMENT_KEYWORDS)
        if elements:
            keyword, elem = elements[0]
            self.log(f"💳 检测到支付按钮: {keyword}")
            if self.click_element_safe(elem, f"支付({keyword})"):
                self.log("🎉 已到达支付页面，抢票流程完成！", "SUCCESS")
                self.last_action_time = time.time()
                return True
        return False

    def run(self):
        """主运行逻辑"""
        options = UiAutomator2Options()
        options.platform_name = 'Android'
        options.udid = '127.0.0.1:16384'
        options.device_name = DEVICE_NAME
        options.app_package = APP_PACKAGE
        options.app_activity = APP_ACTIVITY
        options.no_reset = True
        options.automation_name = 'UiAutomator2'
        options.new_command_timeout = 600

        try:
            self.log("🔌 正在连接Appium服务器...", "INFO")
            self.driver = webdriver.Remote(APPIUM_SERVER_URL, options=options)
            self.log("✅ Appium连接成功", "SUCCESS")

            self.log("🤖 智能抢票引擎 v5.0 已启动", "INFO")
            self.log("📱 请确保猫眼App在前台", "INFO")
            self.log("⏰ 系统将持续监控并自动执行操作\n", "INFO")

            max_inactivity = 300  # 5分钟无操作超时

            while time.time() - self.last_action_time < max_inactivity:
                # 检查倒计时
                countdown = self.check_countdown()
                is_reserved = self.check_reservation()

                if countdown:
                    elapsed = int(time.time() - self.last_action_time)
                    self.log(f"⏰ 倒计时: {countdown} | 等待: {elapsed}秒", "INFO")

                    if is_reserved:
                        self.log("✅ 已预约，持续监控等待开抢...", "INFO")
                        time.sleep(2)
                        self.last_action_time = time.time()
                        continue

                # 按照流程倒序检查（从最后一步开始）
                action_taken = False

                # 5. 支付
                if self.handle_payment():
                    self.log("✅ 抢票成功，已到达支付页面！", "SUCCESS")
                    break

                # 4. 提交订单
                elif self.handle_order_submit():
                    action_taken = True

                # 3. 确认选择
                elif self.handle_confirm_selection():
                    action_taken = True

                # 2. 选择票档
                elif self.handle_ticket_selection():
                    action_taken = True

                # 1. 选择场次
                elif self.handle_date_selection():
                    action_taken = True

                # 0. 初始购买按钮
                elif self.handle_initial_page():
                    action_taken = True

                if not action_taken:
                    elapsed = int(time.time() - self.last_action_time)
                    if elapsed % 10 == 0:  # 每10秒提示一次
                        self.log(f"⏳ 等待可识别操作... ({elapsed}秒)", "INFO")

                    # 尝试刷新
                    if elapsed > 5 and elapsed % 5 == 0:
                        self.smart_refresh()

                time.sleep(0.5)

            # 超时处理
            if time.time() - self.last_action_time >= max_inactivity:
                self.log("⚠️ 5分钟无可识别操作，脚本终止", "WARN")
                self.log("\n可能原因:", "INFO")
                self.log("1. ❌ 无障碍服务未开启（最常见！）", "INFO")
                self.log("   → 手机【设置】->【无障碍】->开启UiAutomator2", "INFO")
                self.log("2. ❌ App未在抢票相关页面", "INFO")
                self.log("3. ❌ 关键字配置不匹配", "INFO")
                self.log("\n💡 建议: 运行【一键诊断.bat】检查配置", "INFO")

        except Exception as e:
            self.log(f"❌ 严重错误: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")

        finally:
            if self.driver:
                self.log("\n📋 操作日志已记录", "INFO")
                self.log("🔌 5秒后断开连接...", "INFO")
                time.sleep(5)
                self.driver.quit()

if __name__ == '__main__':
    grabber = SmartTicketGrabber()
    grabber.run()