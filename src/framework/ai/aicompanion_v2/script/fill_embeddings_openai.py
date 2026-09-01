# scripts/fill_embeddings_openai.py，这个是我临时添加数据用的独立部分。
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()
# 初始化OpenAI客户端（用你的DeepSeek或OpenAI）
client = OpenAI(
    api_key=os.environ.get("SILI_API_KEY"),
    base_url=os.environ.get("SILI_BASE_URL"),  # 如果DeepSeek支持embeddings
)
OPENAI_MODEL = os.environ.get("SILI_Embedding_MODEL")
print(f"client的内容：{client}")
print(f"openai模型：{OPENAI_MODEL}")
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ai_companion"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# 查询空embedding的消息
messages = db.execute(
    text("SELECT id, content FROM ai_messages WHERE embedding IS NULL")
).fetchall()

print(f"📊 找到 {len(messages)} 条需要填充")

for i, (msg_id, content) in enumerate(messages):
    try:
        # 生成1536维向量
        response = client.embeddings.create(
            # model="text-embedding-3-small",  # OpenAI模型，输出1536维
            model=OPENAI_MODEL,
            input=content,
        )
        embedding = response.data[0].embedding

        db.execute(
            # text("UPDATE ai_messages SET embedding = :embedding::vector WHERE id = :id"),
            # {"embedding": embedding, "id": msg_id}
            text(
                "UPDATE ai_messages SET embedding = CAST(:embedding AS vector) WHERE id = :id"
            ),
            {"embedding": embedding, "id": msg_id},
        )

        if (i + 1) % 10 == 0:
            db.commit()
            print(f"  已处理 {i+1}/{len(messages)}")

    except Exception as e:
        print(f"  ❌ 失败: {e}")

db.commit()
print("✅ 完成")
