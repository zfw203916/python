项目：秒杀系统（限量抢购）
核心业务： 100个人抢10张优惠券，使用 Redis + PostgreSQL 保证不超卖。
seckill/
├── models.py          # 数据库模型
├── redis_manager.py   # Redis 管理
├── seckill.py         # 秒杀核心逻辑
├── test.py            # 压力测试


依赖：
psycopg2-binary==2.9.9
redis==5.0.1
asyncpg==0.29.0

用docker:
docker run -d \
  --name postgres15 \
  -e POSTGRES_PASSWORD=123456 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=seckill \
  -p 5432:5432 \
  postgres:15


-- 创建数据库
CREATE DATABASE seckill;

-- 连接数据库
\c seckill;

-- 创建表
CREATE TABLE coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'available', -- 'available', 'sold'
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    sold_at TIMESTAMP
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    coupon_id INTEGER REFERENCES coupons(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 初始化 10 张优惠券
INSERT INTO coupons (code) 
SELECT 'COUPON_' || generate_series(1, 10);



你可以继续扩展
增加用户登录验证

增加限流（每秒限制请求数）

用 WebSocket 推送抢购结果

使用 FastAPI 提供 HTTP 接口

用 Docker Compose 一键部署

