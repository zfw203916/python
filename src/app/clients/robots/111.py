import asyncio
import aiofiles
from playwright.async_api import async_playwright
import lxml.etree as etree
import csv
from io import StringIO
from datetime import datetime


async def get_tiobe_data():
    """
    使用Playwright爬取TIOBE编程语言排行榜数据
    返回解析后的数据列表
    """
    async with async_playwright() as p:
        # 启动浏览器（无头模式）
        browser = await p.chromium.launch(headless=True)

        # 创建浏览器上下文，设置User-Agent避免被识别为爬虫
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 创建新页面
        page = await context.new_page()

        try:
            print("⏳ 正在加载页面...")

            # 访问TIOBE官网，等待网络空闲
            await page.goto(
                "https://www.tiobe.com/tiobe-index/", wait_until="networkidle"
            )

            # 等待表格加载完成（最多等待10秒）
            await page.wait_for_selector("table tbody tr", timeout=10000)
            print("✅ 页面加载完成")

            # 获取渲染后的完整HTML内容
            html = await page.content()

            # 异步保存HTML文件（用于调试）
            async with aiofiles.open(
                "tiobe_playwright.html", "w", encoding="utf-8"
            ) as f:
                await f.write(html)
            print("✅ HTML源码已保存: tiobe_playwright.html")

            # 使用lxml解析HTML
            tree = etree.HTML(html)

            # 使用XPath查找表格行
            rows = tree.xpath("//table/tbody/tr")

            # 如果上面的XPath没找到，尝试备用方案
            if not rows:
                rows = tree.xpath("//table//tr[position()>1]")

            print(f"✅ 找到 {len(rows)} 行数据")

            # 解析表格数据
            data = []
            for row in rows[:20]:  # 只取前20行
                cols = row.xpath("./td")
                if len(cols) >= 6:
                    data.append(
                        {
                            "当前排名": cols[0].text.strip() if cols[0].text else "",
                            "去年排名": cols[1].text.strip()
                            if len(cols) > 1 and cols[1].text
                            else "",
                            "变化": cols[2].text.strip()
                            if len(cols) > 2 and cols[2].text
                            else "",
                            "语言": cols[3].text.strip()
                            if len(cols) > 3 and cols[3].text
                            else "",
                            "评分": cols[4].text.strip()
                            if len(cols) > 4 and cols[4].text
                            else "",
                            "评分变化": cols[5].text.strip()
                            if len(cols) > 5 and cols[5].text
                            else "",
                        }
                    )

            # 如果有数据，保存为CSV文件
            if data:
                # 使用StringIO在内存中构建CSV内容
                csv_buffer = StringIO()

                # 创建CSV写入器
                writer = csv.DictWriter(
                    csv_buffer,
                    fieldnames=[
                        "当前排名",
                        "去年排名",
                        "变化",
                        "语言",
                        "评分",
                        "评分变化",
                    ],
                    quoting=csv.QUOTE_MINIMAL,  # 仅在必要时添加引号
                )

                # 写入表头
                writer.writeheader()

                # 写入数据行
                writer.writerows(data)

                # 获取CSV字符串内容
                csv_content = csv_buffer.getvalue()

                # 使用aiofiles异步写入CSV文件
                async with aiofiles.open("tiobe.csv", "w", encoding="utf-8-sig") as f:
                    await f.write(csv_content)

                print(f"✅ CSV文件已保存: tiobe.csv (共{len(data)}条记录)")

                # 同时生成带时间戳的备份文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"tiobe_{timestamp}.csv"
                async with aiofiles.open(
                    backup_filename, "w", encoding="utf-8-sig"
                ) as f:
                    await f.write(csv_content)
                print(f"✅ 备份文件已保存: {backup_filename}")

                # 在控制台打印前10条数据
                print("\n📊 TIOBE编程语言排行榜 (2026年7月)")
                print("-" * 80)
                print(
                    f"{'排名':<6} {'语言':<15} {'评分':<10} {'变化':<8} {'去年排名':<8}"
                )
                print("-" * 80)
                for item in data[:10]:
                    print(
                        f"{item['当前排名']:<6} {item['语言']:<15} {item['评分']:<10} {item['变化']:<8} {item['去年排名']:<8}"
                    )

                # 返回数据供后续使用
                return data

            else:
                print("⚠️ 未能解析到数据，请检查 tiobe_playwright.html 的表格结构")
                return None

        except asyncio.TimeoutError:
            print("❌ 页面加载超时")
            await page.screenshot(path="timeout_screenshot.png")
            print("📸 已保存超时截图 timeout_screenshot.png")
            return None

        except Exception as e:
            print(f"❌ 发生错误: {e}")
            # 保存错误截图和页面源码
            await page.screenshot(path="error_screenshot.png")
            print("📸 已保存错误截图 error_screenshot.png")

            # 保存错误时的HTML用于调试
            try:
                error_html = await page.content()
                async with aiofiles.open("error_page.html", "w", encoding="utf-8") as f:
                    await f.write(error_html)
                print("📄 已保存错误页面 error_page.html")
            except:
                pass

            return None

        finally:
            # 关闭浏览器释放资源
            await browser.close()
            print("🔚 浏览器已关闭")


async def main():
    """
    主函数，执行爬虫并处理结果
    """
    print("🚀 开始爬取TIOBE编程语言排行榜...")
    print("=" * 60)

    # 执行爬虫
    data = await get_tiobe_data()

    # 处理结果
    if data:
        print("\n✨ 爬取成功！")
        print(f"📊 共获取 {len(data)} 条语言排名数据")
        print("📁 生成文件:")
        print("   - tiobe.csv (主要数据文件)")
        print("   - tiobe_[时间戳].csv (备份文件)")
        print("   - tiobe_playwright.html (页面源码，用于调试)")
    else:
        print("\n❌ 爬取失败，请检查网络连接或网页结构变化")

    print("=" * 60)


# 程序入口
if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
