# test_qdrant.py
"""最小化验证：调用 qdrant-client 的 upsert()"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 1. 连接（宿主机跑 → localhost；容器内跑 → qdrant）
client = QdrantClient(url="http://localhost:6333")

# 2. 建 collection（若已存在会报错，所以先删再建，方便反复测试）
COLLECTION = "test_demo"
if COLLECTION in [c.name for c in client.get_collections().collections]:
    client.delete_collection(COLLECTION)

client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=4, distance=Distance.COSINE),  # 演示用 4 维
)

# 3. ★ 就是这一句 —— 调用库的 upsert()
client.upsert(
    collection_name=COLLECTION,
    points=[
        PointStruct(
            id=1,
            vector=[0.1, 0.2, 0.3, 0.4],
            payload={"name": "测试点1", "content": "你好 Qdrant"},
        ),
        PointStruct(
            id=2,
            vector=[0.9, 0.8, 0.7, 0.6],
            payload={"name": "测试点2", "content": "再见 Qdrant"},
        ),
    ],
    wait=True,
)

# 4. 验证：数一下 collection 里有多少点
info = client.get_collection(COLLECTION)
print(f"✅ 写入完成，points 数量: {info.points_count}")

# 5. 验证：搜索一次
hits = client.query_points(
    collection_name=COLLECTION,
    query=[0.1, 0.2, 0.3, 0.4],
    limit=2,
    with_payload=True,
)
print("🔍 搜索结果：")
for h in hits:
    print(f"  id={h.id} score={h.score:.4f} payload={h.payload}")