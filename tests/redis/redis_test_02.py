import redis
import threading
import time

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
# 2. 启动 Redis
# redis-server
# 初始化库存：1 张票
"""
2、分布式锁（多台机器协作）
场景： 3 个用户同时抢最后 1 张票，不用锁会超卖。
"""
r.set("ticket_count", 1)


def buy_ticket(user_id):
    """模拟买票（不加锁）"""
    count = int(r.get("ticket_count"))
    if count > 0:
        # 模拟网络延迟，让问题更容易暴露
        time.sleep(0.1)
        r.set("ticket_count", count - 1)
        print(f"✅ {user_id} 买票成功！剩余: {count - 1}")
    else:
        print(f"❌ {user_id} 买票失败，已售罄")


def buy_ticket_with_lock(user_id):
    """模拟买票（加 Redis 分布式锁）"""
    lock_key = "ticket_lock"

    # 尝试获取锁（setnx：不存在才设置）
    lock_acquired = r.setnx(lock_key, "locked")
    if not lock_acquired:
        print(f"⏳ {user_id} 没抢到锁，等待...")
        return

    # 设置锁过期时间（防止死锁）
    r.expire(lock_key, 5)

    try:
        # 有了锁，安全操作
        count = int(r.get("ticket_count"))
        if count > 0:
            time.sleep(0.1)
            r.set("ticket_count", count - 1)
            print(f"✅ {user_id} 买票成功！剩余: {count - 1}")
        else:
            print(f"❌ {user_id} 买票失败，已售罄")
    finally:
        # 释放锁
        r.delete(lock_key)


def demo_without_lock():
    """不加锁演示（会超卖）"""
    print("\n" + "=" * 50)
    print("2️⃣ 分布式锁演示（不加锁 → 超卖）")
    print("=" * 50)

    r.set("ticket_count", 1)  # 重置为 1 张票

    # 3 个线程同时抢（模拟 3 台服务器）
    threads = []
    for i in range(3):
        t = threading.Thread(target=buy_ticket, args=(f"用户{i+1}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"💥 最终剩余票数: {r.get('ticket_count')} (本来只有1张，却卖出了多人！)")


def demo_with_lock():
    """加锁演示（正确）"""
    print("\n" + "=" * 50)
    print("3️⃣ 分布式锁演示（加锁 → 正确）")
    print("=" * 50)

    r.set("ticket_count", 1)  # 重置为 1 张票

    threads = []
    for i in range(3):
        t = threading.Thread(target=buy_ticket_with_lock, args=(f"用户{i+1}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"✅ 最终剩余票数: {r.get('ticket_count')} (只有1人买到，正确！)")


# 运行演示
demo_without_lock()
demo_with_lock()
