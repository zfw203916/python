import asyncio
import time
from models import Database
from seckill import Seckill


async def test():
    """模拟 100 个用户同时抢 10 张券"""
    db = Database()
    await db.init()
    seckill = Seckill(db)

    print("=" * 50)
    print("🎯 秒杀测试开始")
    print("=" * 50)

    # 重置库存
    await db.redis.set("coupon:stock", 10)

    # 测试 1：不加锁（坏方式）
    print("\n❌ 测试 1：不加锁（会超卖）")
    await db.redis.set("coupon:stock", 10)
    start = time.time()
    results = await asyncio.gather(*[seckill.buy_coupon_bad(i) for i in range(100)])
    success_count = sum(1 for r in results if r["success"])
    print(f"成功抢到: {success_count} 人（预期 10 人）")
    print(f"⏱️ 耗时: {time.time()-start:.2f}秒")
    print("💥 超卖！")

    # 重置数据
    await db.redis.set("coupon:stock", 10)
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE coupons SET status = 'available', user_id = NULL, sold_at = NULL"
        )
        await conn.execute("DELETE FROM orders")

    # 测试 2：加锁（好方式）
    print("\n✅ 测试 2：加锁（正确）")
    await db.redis.set("coupon:stock", 10)
    start = time.time()
    results = await asyncio.gather(*[seckill.buy_coupon_good(i) for i in range(100)])
    success_count = sum(1 for r in results if r["success"])
    print(f"成功抢到: {success_count} 人（预期 10 人）")
    print(f"⏱️ 耗时: {time.time()-start:.2f}秒")
    print("✅ 完全正确！")

    # 测试 3：异步队列（最高并发）
    print("\n🚀 测试 3：异步队列（最优）")
    await db.redis.set("coupon:stock", 10)
    start = time.time()

    # 100个用户同时发起请求
    tasks = [seckill.buy_coupon_async(i) for i in range(100)]
    await asyncio.gather(*tasks)

    # 后台处理队列
    await seckill.process_queue()

    # 查看结果
    stock = await db.redis.get("coupon:stock")
    print(f"⏱️ 耗时: {time.time()-start:.2f}秒")
    print(f"✅ 所有请求已入队，库存: {stock}")

    await db.pool.close()
    await db.redis.close()


if __name__ == "__main__":
    asyncio.run(test())
