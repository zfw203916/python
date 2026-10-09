from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct

# 连接本地 Qdrant 服务
client = QdrantClient(host="localhost",port=6333)
# 创建一个名为 "my_collection" 的集合
client.create_collection(
    collection_name = "my_collection",
    vectors_config = models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE,
    ),

)
client.upsert(
    collection_name="my_collection",
    points=[
        PointStruct(id=1, vector=[0.05, 0.61, ...], payload={"city": "Berlin", "price": 12}),
        PointStruct(id=2, vector=[0.19, 0.81, ...], payload={"city": "London", "price": 15}),
    ]
)