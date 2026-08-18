import asyncio
# """
# 1. 串行（最笨、最老实）
# 核心思想： 做完 A 再做 B，绝对不插队。
# """

# def task(name, senconds):
#      print(f"👉 {name} 开始")
#      time.sleep(senconds)
#      print(f"✅ {name} 完成")
#      return name

# # 串行执行
# start = time.time()
# task("煮水", 2)
# task("煮面", 2)
# print(f"⏱️ 1、串行,总耗时: {time.time()- start:.1f}秒")
# print("*" * 30)

# """
# 2. 同步阻塞（普通函数调用）
# 核心思想： 调用函数后，原地干等，CPU 空转（虽然 time.sleep 让出了 CPU，但逻辑上被卡住了）。
# 只要用了 time.sleep() 或 requests.get()（网络请求），默认就是同步阻塞。
# """
# def sync_block():
#      print("📞 打电话给客服，开始等待...")
#      time.sleep(3)
#      time.sleep(3)  # 这 3 秒内，程序卡在这里，啥也干不了
#      print("📞 客服说: 好了")
#      return "结果"
# # 这就是你平时最常用的 def 函数，本质上全是同步阻塞
# result = sync_block()
# print(f"2、同步阻塞:{result}")
# print("*" * 30)
# """
# 3. 多线程并发（真·同时抢着干）
# 核心思想： 开启多个线程，大家一起上，让 CPU 快速切换。体现 “并发” 的执行能力。
# 输出： 三个同时开始，同时结束 → 总共 2 秒（而不是 6 秒）。
# 灵魂： 这就是并发！虽然单核 CPU 微观上在切换，但宏观看起来是“同时”。
# 并发（多线程）
# 你一个人（单核CPU）同时吃3碗面：
# 吃一口炸酱面 → 切换到拉面 → 吃一口 → 切换到刀削面 → 吃一口
# 切换速度极快（毫秒级），看起来像同时在吃
# 实际上：任何时刻你嘴里只有一种面
# """
# def concurrency_task(name, seconds):
#     print(f"🏃 {name} 开始跑")
#     time.sleep(seconds)
#     print(f"🏁 {name} 跑完了")

# start = time.time()
# # 核心：同时创建 3 个线程，一起 start
# t1=threading.Thread(target=concurrency_task, args=('线程A', 2))
# t2=threading.Thread(target=concurrency_task, args=('线程B', 2))
# t3=threading.Thread(target=concurrency_task, args=('线程C', 2))

# t1.start(); t2.start(); t3.start()
# t1.join(); t2.join(); t3.join()  # 等他们都干完
# print(f"⏱️ 3. 多线程并发,总耗时: {time.time() - start:.1f}秒")
# print("*" * 30)

# """
# 4. 并行（多核物理同时跑，Python 里不常用）
# 核心思想： 真·同时，必须用 multiprocessing（多进程）。但 Python 有 GIL 锁，多线程没法真正并行，多进程才能吃满多核 CPU。
# 灵魂： 多进程才是真正并行，但开销大，一般只有在处理大量 CPU 计算时用。
# """
# def parallel_task(name):
#     print(f"⚡ {name} 在核心 {os.getpid()} 上真正同时运行")
#     time.sleep(2)

# # 开启 4 个进程，如果你的 CPU 是 4 核，它们就是物理同时跑
# p1 = Process(target=parallel_task, args=("进程1",))
# p2 = Process(target=parallel_task, args=("进程2",))
# p1.start(); p2.start()
# p1.join(); p2.join()
# print("4. 并行")
# print("*" * 30)

"""
5. 异步非阻塞（高并发王牌）⭐
核心思想： 发起任务后不等结果，立即返回去做别的。等结果准备好了，再回来处理（回调/事件循环）。这是你现在最应该学会的！
总耗时仅 3 秒（耗时最长的那一个）。
灵魂： 这里的 await 不是等待，而是“切出去” 的意思！这是异步非阻塞最反直觉、也最核心的点。
"""


async def async_task(name, seconds):
    print(f"🚀 {name} 发起请求，不等了，去干别的")
    await asyncio.sleep(seconds)  # 关键！await 代表“切出去”，不阻塞
    print(f"🎉 {name} 结果回来了，继续处理")
    return name


async def main():
    # 核心：同时创建 3 个任务，但不等待，全部并发执行
    task1 = asyncio.create_task(async_task("任务1", 2))
    task2 = asyncio.create_task(async_task("任务2", 1))
    task3 = asyncio.create_task(async_task("任务3", 3))

    # 等待所有任务完成
    results = await asyncio.gather(task1, task2, task3)
    print(f"全部完成: {results}")


# 运行异步事件循环
asyncio.run(main())
