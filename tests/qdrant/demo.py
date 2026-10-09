from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

# ========== 1. 准备数据（模拟你的电影库）==========
movies = [
    {"id": 1, "title": "海底总动员", "desc": "一位父亲跨越海洋寻找失踪的儿子", "year": 2003},
    {"id": 2, "title": "当幸福来敲门", "desc": "父亲带着儿子度过贫困，努力奋斗改变命运", "year": 2006},
    {"id": 3, "title": "速度与激情", "desc": "街头赛车手与警察的飙车故事", "year": 2001},
    {"id": 4, "title": "星际穿越", "desc": "父亲穿越虫洞拯救人类，与女儿跨越时空的羁绊", "year": 2014},
    {"id": 5, "title": "疯狂动物城", "desc": "兔子警官和狐狸搭档破案", "year": 2016},
]

# ========== 2. 加载嵌入模型（把文字转成向量）==========
print("正在加载模型...")
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384维，轻量快速
VECTOR_SIZE = 384  # 这个模型的向量维度固定为384

# ========== 3. 初始化 Qdrant（内存模式，无需服务器）==========
client = QdrantClient(":memory:")

# ========== 4. 创建集合（类似建表）==========
client.create_collection(
    collection_name="movies",
    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
)
print("✅ 集合创建完成")

# ========== 5. 把电影转成向量并存入 ==========
points = []
for m in movies:
    # 把描述文字转成向量
    vector = model.encode(m["desc"]).tolist()
    points.append(
        PointStruct(
            id=m["id"],
            vector=vector,
            payload={"title": m["title"], "year": m["year"], "desc": m["desc"]},
        )
    )

client.upsert(collection_name="movies", points=points)
print(f"✅ 已存入 {len(points)} 部电影")

# ========== 6. 语义搜索 ==========
def search(query, year_filter=None, top_k=3):
    query_vector = model.encode(query).tolist()

    # 可选：加年份过滤条件（元数据过滤）
    query_filter = None
    if year_filter:
        query_filter = Filter(
            must=[FieldCondition(key="year", range={"gte": year_filter})]
        )

    results = client.query_points(
        collection_name="movies",
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    ).points

    print(f"\n🔍 查询：「{query}」" + (f"（{year_filter}年后）" if year_filter else ""))
    for r in results:
        print(f"  相似度 {r.score:.3f} | {r.payload['title']} ({r.payload['year']}) | {r.payload['desc']}")

# ========== 7. 测试 ==========
search("父爱和亲情的故事")          # 期望：海底总动员、当幸福来敲门、星际穿越
search("赛车飙车")                  # 期望：速度与激情
search("亲情", year_filter=2010)    # 期望：星际穿越（2014）、疯狂动物城（2016）