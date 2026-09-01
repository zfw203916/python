"""
# 低并发:1个人点餐
服务员: 你好,要点什么？
顾客: 我要一份炒饭
服务员: 好的,请稍等(5分钟后端上来)

# 高并发:1000人同时点餐
1000个顾客同时喊:"我要炒饭！"
系统必须同时处理1000个订单


高并发秒杀系统
场景:10000人同时抢10张电影票
技术:asyncio + Redis + 连接池
"""

import asyncio
import time
import redis.asyncio as aioredis
from datetime import datetime
from redis.retry import Retry
from redis.backoff import ExponentialBackoff

# ============ 配置 ============
TOTAL_TICKETS = 5
TOTAL_USERS = 100
REDIS_URL = "redis://localhost:6379"


# ============ Redis 操作 ============
async def init_redis():
    """连接Redis"""
    retry_again = Retry(ExponentialBackoff(cap=1, base=0.1), retries=3)
    redis = await aioredis.from_url(
        REDIS_URL,
        max_connections=100,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry=retry_again,
    )
    return redis


async def reset_tickets(redis):
    """重置库存"""
    await redis.set("tickets", TOTAL_TICKETS)
    await redis.delete("orders")


async def get_tickets(redis):
    """查询剩余票数"""
    return int(await redis.get("tickets") or 0)


# ============ 秒杀逻辑（高并发核心） ============
async def seckill(user_id: int, redis):
    """
    高并发扣减库存
    使用 Redis 原子操作 DECR，避免并发问题
    """
    # 1. Redis 原子操作减库存（这一行就是高并发关键）
    remaining = await redis.decr("tickets")
    # 超卖了，回滚
    if remaining < 0:
        await redis.incr("tickets")
        return {"user": user_id, "status": "fail", "msg": "已抢完"}
    # 2. 记录订单（异步写入，不阻塞）
    order_id = f"order_{user_id}_{int(time.time())}"
    await redis.lpush("orders", order_id)
    await asyncio.sleep(0.001)
    return {"user": user_id, "status": "success", "msg": f"抢到第{remaining+1}张票"}


# 添加限流，防止Redis过载
SEMAPHORE_LIMIT = 500
semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)


async def worker(user_id: int, redis, results: list):
    """单个用户的抢票任务"""
    """带限流的抢票任务"""
    async with semaphore:
        result = await seckill(user_id, redis)
        results.append(result)
        if result["status"] == "success":
            print(f"✅ 用户{user_id} 抢到了！剩余{result['msg']}")
        else:
            pass  # 失败不打印，减少刷屏


async def run_seckill():
    """高并发压测"""
    redis = await init_redis()
    await reset_tickets(redis)
    print(f"🎬 开始秒杀：{TOTAL_USERS}人抢{TOTAL_TICKETS}张票")
    print(f"⏰ 开始时间：{datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    start_time = time.time()
    # 创建10000个协程任务
    results = []
    tasks = [worker(i, redis, results) for i in range(TOTAL_USERS)]

    # 全部并发执行
    await asyncio.gather(*tasks)
    end_time = time.time()
    end_time_str = datetime.fromtimestamp(end_time).strftime("%H:%M:%S.%f")[:-3]
    print(f"⏰ 结束时间：{end_time_str}")

    # ============ 统计结果 ============
    success_count = sum(1 for r in results if r["status"] == "success")
    fail_count = sum(1 for r in results if r["status"] == "fail")

    print("\n📊 ===== 秒杀结果 =====")
    print(f"✅ 成功抢到：{success_count}人")
    print(f"❌ 未抢到：{fail_count}")
    print(f"🎫 剩余票数：{await get_tickets(redis)}")
    print(f"⏱️  总耗时：{(end_time - start_time):.2f}秒")
    print(f"🚀 QPS： {TOTAL_USERS/(end_time - start_time):.0f}请求/秒 ")


if __name__ == "__main__":
    asyncio.run(run_seckill())
