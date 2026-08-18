"""
程序执行方式完整对比演示
包含：同步阻塞、多线程并发、多进程并行、异步非阻塞、并发加锁
"""

import os
import time
import threading
import asyncio
from multiprocessing import Process


# ==================== 1. 同步阻塞 ====================
def sync_block_task(name, seconds):
    """同步阻塞：站着死等，啥也不干"""
    print(f"📞 [{name}] 开始执行，我要等 {seconds} 秒...")
    time.sleep(seconds)  # 这行代码卡住，程序动不了
    print(f"📞 [{name}] 执行完成！")
    return f"{name}的结果"


def demo_sync_block():
    print("\n" + "=" * 50)
    print("1️⃣ 同步阻塞演示（普通函数调用）")
    print("=" * 50)
    start = time.time()

    # 串行执行，一个接一个
    result1 = sync_block_task("任务A", 2)
    result2 = sync_block_task("任务B", 2)

    print(f"⏱️ 总耗时: {time.time() - start:.1f}秒")
    print(f"📦 结果: {result1}, {result2}")
    print("💡 核心思想: 调用函数后原地死等，CPU虽然释放了，但逻辑被卡住")


# ==================== 2. 多线程并发 ====================
def concurrency_task(name, seconds):
    """多线程并发：大家同时开始，宏观一起动"""
    print(f"🏃 [{name}] 开始执行，耗时 {seconds} 秒")
    time.sleep(seconds)
    print(f"🏁 [{name}] 执行完成！")


def demo_concurrency():
    print("\n" + "=" * 50)
    print("2️⃣ 多线程并发演示（线程同时启动）")
    print("=" * 50)
    start = time.time()

    # 创建 3 个线程，同时启动
    threads = []
    for i in range(3):
        t = threading.Thread(target=concurrency_task, args=(f"线程{i+1}", 2))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    print(f"⏱️ 总耗时: {time.time() - start:.1f}秒")
    print('💡 核心思想: 多个线程同时执行，宏观看起来是"一起干"')
    print("💡 注意: Python 因为有 GIL，多线程适合 IO 密集型任务")


# ==================== 3. 多进程并行 ====================
def parallel_task(name, seconds):
    """多进程并行：真正的物理同时执行"""
    pid = os.getpid()  # 获取当前进程 ID
    print(f"⚡ [{name}] 在进程 {pid} 上开始执行，耗时 {seconds} 秒")
    time.sleep(seconds)
    print(f"⚡ [{name}] 在进程 {pid} 上执行完成！")


def demo_parallel():
    print("\n" + "=" * 50)
    print("3️⃣ 多进程并行演示（真正物理同时）")
    print("=" * 50)
    start = time.time()

    # 创建 2 个进程，真·同时执行（如果 CPU 是多核）
    p1 = Process(target=parallel_task, args=("进程A", 2))
    p2 = Process(target=parallel_task, args=("进程B", 2))

    p1.start()
    p2.start()
    p1.join()
    p2.join()

    print(f"⏱️ 总耗时: {time.time() - start:.1f}秒")
    print("💡 核心思想: 多进程利用多核CPU，物理上真正同时执行")
    print("💡 注意: 进程开销大，适合 CPU 密集型计算任务")


# ==================== 4. 异步非阻塞 ====================
async def async_task(name, seconds):
    """异步非阻塞：不等结果，好了叫我"""
    print(f"🚀 [{name}] 发起请求，耗时 {seconds} 秒，不等了去干别的")
    await asyncio.sleep(seconds)  # 关键：await 是"切出去"，不是等待！
    print(f"🎉 [{name}] 结果回来了，继续处理")
    return f"{name}的结果"


async def demo_async_core():
    """异步的核心演示"""
    print("\n" + "=" * 50)
    print("4️⃣ 异步非阻塞演示（高并发王牌）")
    print("=" * 50)
    start = time.time()

    # 同时创建 3 个异步任务，全部并发执行
    task1 = asyncio.create_task(async_task("任务1", 3))
    task2 = asyncio.create_task(async_task("任务2", 1))
    task3 = asyncio.create_task(async_task("任务3", 2))

    # 等待所有任务完成
    results = await asyncio.gather(task1, task2, task3)

    print(f"⏱️ 总耗时: {time.time() - start:.1f}秒")
    print(f"📦 结果: {results}")
    print("💡 核心思想: await 是'切出去'而不是'等待'，事件循环调度")


def demo_async():
    """运行异步演示"""
    asyncio.run(demo_async_core())


# ==================== 5. 并发加锁 ====================
def unsafe_increment(counter, times):
    """不加锁的危险操作"""
    for _ in range(times):
        counter[0] += 1  # 这不是原子操作，会出问题


def safe_increment(counter, times, lock):
    """加锁的安全操作"""
    for _ in range(times):
        lock.acquire()  # 🔒 加锁
        counter[0] += 1
        lock.release()  # 🔓 释放锁


def demo_lock():
    print("\n" + "=" * 50)
    print("5️⃣ 并发加锁演示（保证数据一致性）")
    print("=" * 50)

    # 不加锁的版本（会出错）
    print("\n❌ 不加锁的情况（数据混乱）：")
    unsafe_counter = [0]
    threads = []
    for _ in range(5):
        t = threading.Thread(target=unsafe_increment, args=(unsafe_counter, 10000))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    print(f"   期望值: 50000, 实际值: {unsafe_counter[0]}")  # 大概率不是 50000

    # 加锁的版本（正确）
    print("\n✅ 加锁的情况（数据正确）：")
    safe_counter = [0]
    lock = threading.Lock()
    threads = []
    for _ in range(5):
        t = threading.Thread(target=safe_increment, args=(safe_counter, 10000, lock))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    print(f"   期望值: 50000, 实际值: {safe_counter[0]}")  # 稳稳 50000

    print("💡 核心思想: 多线程抢资源时必须加锁，保证同一时刻只有一个人改")


# ==================== 6. 异步 vs 同步 直观对比 ====================
def demo_sync_vs_async():
    """直观对比同步和异步的效率"""
    print("\n" + "=" * 50)
    print("6️⃣ 同步 vs 异步 效率对比")
    print("=" * 50)

    # 同步版本
    print("\n🐢 同步执行（一个一个来）：")
    start = time.time()
    for i in range(3):
        time.sleep(1)  # 假装每个任务耗时 1 秒
        print(f"   同步任务 {i+1} 完成")
    print(f"   总耗时: {time.time() - start:.1f}秒")

    # 异步版本
    print("\n🚀 异步执行（全部同时发起）：")

    async def async_demo():
        start = time.time()
        tasks = [asyncio.sleep(1) for _ in range(3)]  # 假装 3 个异步任务
        await asyncio.gather(*tasks)
        print(f"   总耗时: {time.time() - start:.1f}秒")

    asyncio.run(async_demo())
    print("💡 核心思想: 同样 3 个耗时任务，同步要 3 秒，异步只要 1 秒！")


# ==================== 主程序 ====================
def main():
    """运行所有演示"""
    print("🎯 程序执行方式完整对比演示")
    print("作者：Python 程序员")
    print("时间：2026年")

    # 依次运行各个演示
    demo_sync_block()
    demo_concurrency()
    demo_parallel()
    demo_async()
    demo_lock()
    demo_sync_vs_async()

    print("\n" + "=" * 50)
    print("🎉 所有演示完成！")
    print("=" * 50)
    print("\n📚 学习要点总结：")
    print("1. 同步阻塞: 站着死等，最常用但效率低")
    print("2. 多线程并发: 宏观一起干，适合 IO 密集型")
    print("3. 多进程并行: 物理同时跑，适合 CPU 密集型")
    print("4. 异步非阻塞: await 是切出，现代高并发首选")
    print("5. 并发加锁: 抢资源时的安全机制")


if __name__ == "__main__":
    main()
