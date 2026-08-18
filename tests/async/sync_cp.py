import asyncio
import time


# ============ 模拟耗时操作（异步版本） ============
async def cook_dish(dish_name, cook_time):
    """模拟厨师做菜 - 异步版本"""
    print(f"👨‍🍳 开始做 {dish_name}，需要 {cook_time} 秒")

    # 核心：await 让出控制权，等待期间 CPU 可以干别的
    await asyncio.sleep(cook_time)  # 模拟耗时 I/O

    print(f"✅ {dish_name} 做好了！")
    return f"{dish_name}（耗时{cook_time}秒）"


# ============ 异步主函数 ============
async def main_async():
    """异步方式：同时做多道菜"""
    print("=" * 40)
    print("【异步模式】同时下锅 3 道菜")
    print("=" * 40)

    start = time.time()

    # 核心：同时创建 3 个任务，不等待任何一个完成
    task1 = asyncio.create_task(cook_dish("红烧肉", 3))
    task2 = asyncio.create_task(cook_dish("清蒸鱼", 2))
    task3 = asyncio.create_task(cook_dish("炒青菜", 1))

    # 核心：await 等待所有任务完成
    results = await asyncio.gather(task1, task2, task3)

    end = time.time()
    print(f"\n🍽️ 所有菜上齐：{results}")
    print(f"⏱️ 总耗时：{end - start:.1f} 秒\n")


# ============ 同步对比函数 ============
def main_sync():
    """同步方式：一道一道做"""
    print("=" * 40)
    print("【同步模式】一道一道做")
    print("=" * 40)

    start = time.time()

    # 核心：必须等前一道做完才能做下一道
    result1 = cook_dish_sync("红烧肉", 3)
    result2 = cook_dish_sync("清蒸鱼", 2)
    result3 = cook_dish_sync("炒青菜", 1)

    end = time.time()
    print(f"\n🍽️ 所有菜上齐：{result1}, {result2}, {result3}")
    print(f"⏱️ 总耗时：{end - start:.1f} 秒\n")


def cook_dish_sync(dish_name, cook_time):
    """同步版本的做菜（模拟阻塞）"""
    print(f"👨‍🍳 开始做 {dish_name}，需要 {cook_time} 秒")
    time.sleep(cook_time)  # 阻塞：CPU 在这干等
    print(f"✅ {dish_name} 做好了！")
    return f"{dish_name}（耗时{cook_time}秒）"


# ============ 运行入口 ============
if __name__ == "__main__":
    # 运行同步版本
    main_sync()

    # 运行异步版本
    asyncio.run(main_async())
