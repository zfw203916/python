"""
自动化测试脚本：使用Python + Playwright 在百度搜索“北京烤鸭”
作者：自动化测试工程师小白
日期：2026-08-17
修复：解决百度搜索框不可见问题，使用多种替代方案
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time


def run_baidu_search_v1():
    """
    方案1：使用键盘事件模拟搜索（最稳定）
    不依赖点击按钮，使用回车键触发搜索
    """
    with sync_playwright() as p:
        # 1. 启动浏览器
        browser = p.chromium.launch(headless=False, channel="chrome")
        print("✅ 浏览器启动成功")

        context = browser.new_context()
        page = context.new_page()

        # 2. 打开百度首页
        page.goto("https://www.baidu.com")
        print("✅ 已打开百度首页")

        # 等待页面基本加载完成
        page.wait_for_load_state("networkidle")
        print("✅ 页面加载完成")

        # 3. 使用JavaScript直接操作DOM输入内容
        # 方法：通过evaluate直接在页面上执行JS代码
        page.evaluate("""
            // 直接设置搜索框的值
            const searchInput = document.querySelector('#kw');
            if (searchInput) {
                searchInput.value = '北京烤鸭';
                // 触发input事件，让页面感知到内容变化
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        """)
        print("✅ 已通过JavaScript输入：北京烤鸭")

        # 4. 使用回车键触发搜索（而不是点击按钮）
        # 先聚焦到搜索框
        page.evaluate("document.querySelector('#kw').focus()")
        # 然后按下回车键
        page.keyboard.press("Enter")
        print("✅ 已按回车键触发搜索")

        # 等待搜索结果加载
        page.wait_for_selector("h3", state="visible", timeout=10000)
        print("✅ 搜索结果已加载")

        # 观察结果
        time.sleep(3)

        # 5. 关闭浏览器
        browser.close()
        print("✅ 浏览器已关闭")


def run_baidu_search_v2():
    """
    方案2：直接构造搜索URL（最快速）
    绕过首页交互，直接访问搜索结果的URL
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        print("✅ 浏览器启动成功")

        context = browser.new_context()
        page = context.new_page()

        # 直接构造百度搜索URL并访问
        search_keyword = "北京烤鸭"
        search_url = f"https://www.baidu.com/s?wd={search_keyword}"

        page.goto(search_url)
        print(f"✅ 直接访问搜索URL: {search_url}")

        # 等待搜索结果加载
        page.wait_for_selector("h3", state="visible", timeout=10000)
        print("✅ 搜索结果已加载")

        # 验证搜索框中的内容是否正确
        search_value = page.evaluate("document.querySelector('#kw')?.value || ''")
        print(f"✅ 搜索框内容验证: {search_value}")

        # 观察结果
        time.sleep(3)

        # 关闭浏览器
        browser.close()
        print("✅ 浏览器已关闭")


def run_baidu_search_v3():
    """
    方案3：使用Playwright的fill方法并配合强制操作
    使用更底层的API绕过可见性检查
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        print("✅ 浏览器启动成功")

        context = browser.new_context()
        page = context.new_page()

        # 打开百度首页
        page.goto("https://www.baidu.com")
        print("✅ 已打开百度首页")

        # 等待页面加载完成
        page.wait_for_load_state("networkidle")
        print("✅ 页面加载完成")

        # 使用更底层的DOM操作
        # 先通过evaluate找到并操作元素
        page.evaluate("""
            // 强制显示搜索框
            const kw = document.querySelector('#kw');
            if (kw) {
                // 移除任何可能隐藏元素的样式
                kw.style.display = 'block';
                kw.style.visibility = 'visible';
                kw.style.opacity = '1';
                kw.value = '北京烤鸭';
                // 触发事件
                kw.dispatchEvent(new Event('input', { bubbles: true }));
                kw.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            // 强制显示搜索按钮
            const su = document.querySelector('#su');
            if (su) {
                su.style.display = 'block';
                su.style.visibility = 'visible';
                su.style.opacity = '1';
            }
        """)
        print("✅ 已强制显示元素并输入内容")

        # 直接使用JS点击搜索按钮
        page.evaluate("document.querySelector('#su').click()")
        print("✅ 已通过JavaScript点击搜索按钮")

        # 等待搜索结果
        page.wait_for_selector("h3", state="visible", timeout=10000)
        print("✅ 搜索结果已加载")

        time.sleep(3)
        browser.close()
        print("✅ 浏览器已关闭")


def run_baidu_search_v4():
    """
    方案4：使用最稳定的组合方案
    结合了多种技术，确保在各种情况下都能工作
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        print("✅ 浏览器启动成功")

        context = browser.new_context()
        page = context.new_page()

        # 打开百度首页
        page.goto("https://www.baidu.com")
        print("✅ 已打开百度首页")

        # 使用最稳定的等待策略
        try:
            # 等待页面完全加载
            page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass

        # 方法：组合使用多种技术
        # 1. 先用JS直接操作DOM
        page.evaluate("""
            // 确保搜索框存在并设置值
            const kw = document.querySelector('#kw');
            if (kw) {
                kw.value = '北京烤鸭';
                kw.dispatchEvent(new Event('input', { bubbles: true }));
                // 聚焦到搜索框
                kw.focus();
            }
        """)
        print("✅ 已通过JS设置搜索内容")

        # 2. 使用键盘操作（不受元素可见性影响）
        # 因为已经聚焦，直接使用键盘输入可以确保内容正确
        page.keyboard.press("Control+A")  # 全选
        page.keyboard.press("Backspace")  # 删除
        page.keyboard.type("北京烤鸭")  # 重新输入（确保内容正确）
        print("✅ 已通过键盘输入：北京烤鸭")

        # 3. 使用回车键触发搜索
        page.keyboard.press("Enter")
        print("✅ 已按回车键搜索")

        # 4. 等待搜索结果
        try:
            page.wait_for_selector("h3", state="visible", timeout=10000)
            print("✅ 搜索结果已加载")
        except PlaywrightTimeoutError:
            # 如果等待超时，尝试使用备选选择器
            page.wait_for_selector(".result", state="visible", timeout=5000)
            print("✅ 通过备选选择器找到搜索结果")

        # 5. 截图保存结果（验证用）
        page.screenshot(path="baidu_search_result.png")
        print("✅ 已保存截图：baidu_search_result.png")

        time.sleep(2)
        browser.close()
        print("✅ 浏览器已关闭")


if __name__ == "__main__":
    print("🚀 开始执行百度搜索自动化测试...")
    print("=" * 50)

    # 选择最稳定的方案执行
    print("📌 使用方案4：最稳定的组合方案")
    run_baidu_search_v4()

    # 如果方案4有问题，可以尝试其他方案：
    # print("📌 使用方案1：键盘事件模拟")
    # run_baidu_search_v1()

    # print("📌 使用方案2：直接构造搜索URL")
    # run_baidu_search_v2()

    # print("📌 使用方案3：JavaScript强制操作")
    # run_baidu_search_v3()
