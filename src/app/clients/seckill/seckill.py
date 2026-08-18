import asyncio
import time
from models import Database


class Seckill:
    def __init__(self, db: Database):
        self.db = db

    async def buy_coupon_bad(self, user_id: int):
        """❌ 错误示范：不加锁，会超卖"""
        # 1. 查库存（从 Redis）
        stock = await self.db.redis.get("coupon:stock")
        if not stock or int(stock) <= 0:
            return {"success": False, "msg": "已售罄"}

        # 2. 模拟网络延迟
        await asyncio.sleep(0.1)

        # 3. 扣库存
        new_stock = int(stock) - 1
        await self.db.redis.set("coupon:stock", new_stock)

        # 4. 记录订单（写入数据库）
        async with self.db.pool.acquire() as conn:
            # 查找一张可用优惠券
            coupon = await conn.fetchrow(
                "SELECT id FROM coupons WHERE status = 'available' LIMIT 1"
            )
            if coupon:
                await conn.execute(
                    "UPDATE coupons SET status = 'sold', user_id = $1, sold_at = NOW() "
                    "WHERE id = $2",
                    user_id,
                    coupon["id"],
                )
                await conn.execute(
                    "INSERT INTO orders (user_id, coupon_id, status) VALUES ($1, $2, 'success')",
                    user_id,
                    coupon["id"],
                )
                return {"success": True, "msg": f"用户{user_id}抢到优惠券"}
        return {"success": False, "msg": "已售罄"}

    async def buy_coupon_good(self, user_id: int):
        """✅ 正确示范：使用 Redis 分布式锁"""
        lock_key = "seckill:lock"

        # 1. 尝试获取锁（setnx + 过期时间）
        lock_acquired = await self.db.redis.setnx(lock_key, "locked")
        if not lock_acquired:
            return {"success": False, "msg": "系统繁忙，请重试"}

        # 设置锁过期时间（防止死锁）
        await self.db.redis.expire(lock_key, 3)

        try:
            # 2. 检查库存（原子操作）
            stock = await self.db.redis.decr("coupon:stock")
            if stock < 0:
                # 库存不足，恢复
                await self.db.redis.incr("coupon:stock")
                return {"success": False, "msg": "已售罄"}

            # 3. 记录订单（写入数据库）
            async with self.db.pool.acquire() as conn:
                async with conn.transaction():
                    coupon = await conn.fetchrow(
                        "SELECT id FROM coupons WHERE status = 'available' LIMIT 1 FOR UPDATE"
                    )
                    if coupon:
                        await conn.execute(
                            "UPDATE coupons SET status = 'sold', user_id = $1, sold_at = NOW() "
                            "WHERE id = $2",
                            user_id,
                            coupon["id"],
                        )
                        await conn.execute(
                            "INSERT INTO orders (user_id, coupon_id, status) VALUES ($1, $2, 'success')",
                            user_id,
                            coupon["id"],
                        )
                        return {"success": True, "msg": f"用户{user_id}抢到优惠券"}

            return {"success": False, "msg": "抢券失败"}

        finally:
            # 4. 释放锁
            await self.db.redis.delete(lock_key)

    async def buy_coupon_async(self, user_id: int):
        """🚀 进阶：异步非阻塞 + 消息队列"""
        # 直接用 Redis 列表做队列（异步解耦）
        await self.db.redis.lpush("seckill:queue", f"{user_id}:{int(time.time())}")
        return {"success": True, "msg": f"用户{user_id}已进入排队"}

    async def process_queue(self):
        """后台异步处理队列（消费者）"""
        while True:
            # 从队列取任务
            task = await self.db.redis.rpop("seckill:queue")
            if not task:
                await asyncio.sleep(0.1)
                continue

            user_id = task.split(":")[0]
            result = await self.buy_coupon_good(int(user_id))

            # 存入结果队列（通知用户）
            await self.db.redis.lpush("seckill:result", f"{user_id}:{result['msg']}")
