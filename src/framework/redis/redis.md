# docker-compose up -d
# 测试 Redis
docker exec -it ai-companion-redis redis-cli ping

# 设置测试数据
docker exec -it ai-companion-redis redis-cli set test "AI Companion"
docker exec -it ai-companion-redis redis-cli get test


# docker exec -it redis-server redis-cli