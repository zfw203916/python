import redis
import time

# 连接 Redis
# 速度问题（缓存，单机必用）
"""
缓存（单机加速）
场景： 查数据库很慢（假设2秒），用 Redis 缓存后飞快（1ms）。
"""
r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def get_user_info(user_id):
    """模拟查数据库，很慢（2秒）"""
    print(f"🐢 查询数据库: 用户 {user_id}")
    time.sleep(2)  # 模拟数据库查询耗时
    return f"用户{user_id}的数据"


def get_user_with_cache(user_id):
    """先查缓存，没有再查数据库"""
    cache_key = f"user:{user_id}"

    # 1️⃣ 先查 Redis
    cached_data = r.get(cache_key)
    if cached_data:
        print(f"⚡ 命中缓存: {cached_data} (耗时 1ms)")
        return cached_data

    # 2️⃣ 缓存没有，查数据库
    data = get_user_info(user_id)

    # 3️⃣ 存入 Redis，设置过期时间 60 秒
    r.set(cache_key, data, ex=60)  # 新写法（ex=60 表示60秒过期）
    print(f"💾 已缓存: {data}")
    return data


# 测试
print("=" * 50)
print("1️⃣ Redis 缓存演示")
print("=" * 50)

start = time.time()
get_user_with_cache(1)  # 第一次：查数据库（2秒）
print(f"第一次耗时: {time.time() - start:.2f}秒\n")

start = time.time()
get_user_with_cache(1)  # 第二次：直接命中缓存（1ms）
print(f"第二次耗时: {time.time() - start:.2f}秒")
