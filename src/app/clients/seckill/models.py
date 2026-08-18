import asyncpg
import redis.asyncio as aioredis


class Database:
    def __init__(self):
        self.pool = None
        self.redis = None

    async def init(self):
        """初始化连接池"""
        self.pool = await asyncpg.create_pool(
            host="localhost",
            port=5432,
            user="postgres",
            password="123456",
            database="seckill",
            min_size=5,
            max_size=20,
        )

        self.redis = await aioredis.from_url(
            "redis://localhost:6379/0", decode_responses=True
        )

        # 预热 Redis 缓存
        await self.init_cache()

    async def init_cache(self):
        """将库存预热到 Redis"""
        async with self.pool.acquire() as conn:
            # 查询可用优惠券数量
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM coupons WHERE status = 'available'"
            )
            await self.redis.set("coupon:stock", count)
            await self.redis.set("coupon:total", count)
            print(f"✅ 库存预热完成: {count} 张")
