import asyncio
from playwright.async_api import async_playwright, TimeoutError

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 打开猫眼登录页面
        await page.goto("https://passport.maoyan.com/pc/login")
        
        print("请使用手机猫眼APP扫码登录...")
        
        # 1. 等待用户扫码登录，然后页面会跳转回主页
        print("请使用手机猫眼APP扫码登录...")
        
        # 2. 等待页面导航到主页，并给予足够的时间让页面完全加载
        try:
            # 等待URL变为猫眼主页，最长等待2分钟
            page.wait_for_url("https://www.maoyan.com/", timeout=120000)
            print("页面已成功跳转回主页。")
            # 等待网络空闲，确保所有动态内容加载完成
            page.wait_for_load_state("networkidle", timeout=60000)
            print("页面网络已稳定。")
        except Exception as e:
            print(f"等待页面跳转或加载失败: {e}")
            print(f"当前页面URL: {page.url}")
            print("将继续尝试验证登录状态...")

        # 3. 使用循环和延时来稳定地检查登录状态
        login_success = False
        for i in range(30): # 尝试30次，总计最多等待30秒
            # 检查用户头像是否存在，这是最可靠的登录标志
            avatar = page.locator(".header-user-avatar")
            if avatar.is_visible():
                print("检测到用户头像，登录成功！")
                try:
                    # 鼠标悬停以显示用户名
                    avatar.hover()
                    user_name_element = page.locator(".header-user-name")
                    user_name_element.wait_for(state="visible", timeout=5000)
                    user_name = user_name_element.inner_text()
                    print(f"欢迎您，{user_name}！")
                    login_success = True
                    break # 登录成功，跳出循环
                except Exception as e:
                    print(f"获取用户名失败: {e}")
                    # 即使获取用户名失败，只要头像存在，也认为登录成功
                    login_success = True
                    break
            else:
                # 如果头像未出现，等待1秒后重试
                print(f"未检测到登录状态，正在重试... (第{i+1}/30次)")
                page.wait_for_timeout(1000)

        # 4. 根据登录结果进行后续操作
        if login_success:
            print("登录成功，将尝试进入演唱会详情页...")
            # 跳转到演出列表页
            await page.goto("https://www.gewara.com/list/0", wait_until="networkidle")
            print("已跳转到演出列表页。")

            try:
                # 定位到包含特定演唱会信息的整个项目容器
                print("正在定位演唱会项目...")
                concert_container = page.locator("div.list-item", has=page.locator("h3:has-text('周杰伦2025“嘉年华”世界巡回演唱会-武汉站')"))
                
                # 等待元素可见
                await concert_container.wait_for(state="visible", timeout=30000)
                print("已定位到演唱会项目。")

                # 在该项目内找到“购票”按钮
                buy_button = concert_container.locator("a.btn-buy")
                
                is_visible = await buy_button.is_visible()
                if is_visible:
                    print("找到购票按钮，正在点击...")
                    await buy_button.click()
                else:
                    print("“购票”按钮不可见，将尝试点击整个项目区域...")
                    await concert_container.click()

                # 等待页面跳转或发生变化
                print("等待页面响应...")
                await page.wait_for_load_state("domcontentloaded", timeout=60000)
                
                print(f"点击后，当前页面URL为: {page.url}")
                print("请检查浏览器页面，确认是否进入了购票流程。")
                await page.screenshot(path='after_click_buy.png')
                print("已保存点击后的页面截图至 after_click_buy.png")

            except Exception as e:
                print(f"点击购票按钮或项目失败: {e}")
                await page.screenshot(path='buy_button_click_failed.png')
                print("已保存当前页面截图至 buy_button_click_failed.png")
        
        else:
            print("在30秒内未能确认登录状态，脚本将退出。")
            await page.screenshot(path='login_debug.png')
            print("已保存当前页面截图至 login_debug.png，请查看以了解问题。")

        # Keep the browser open for a while for observation
        print("脚本执行完毕，浏览器将保持打开状态以便观察。")
        await page.wait_for_timeout(300000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())