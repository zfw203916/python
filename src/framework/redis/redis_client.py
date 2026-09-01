import redis

# 连接 Redis
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# 测试连接
print(r.ping())  # True

# 设置和获取
r.set("name", "Redis Demo")
print(r.get("name"))  # Redis Demo

# 设置过期时间（10秒）
r.setex("temp_key", 10, "value")

# 列表操作
r.lpush("mylist", "item1", "item2")
print(r.lrange("mylist", 0, -1))

# 哈希操作
r.hset("user:1", mapping={"name": "John", "age": 30})
print(r.hgetall("user:1"))
