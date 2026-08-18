#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从零构建RAG（检索增强生成）完整原型
包含四个任务：
  任务一：无依赖文本切分
  任务二：极简关键词搜索引擎
  任务三：手动封装AI问答函数
  任务四：引入向量替换关键词

使用方法：
  1. 确保 news.txt 与本文件在同一目录
  2. 任务一/二/三可直接运行（任务三需配置API Key）
  3. 任务四需先安装：pip install sentence-transformers
  4. 运行：python rag_demo.py
"""

import os
import re
import math
import pickle
from typing import List, Tuple, Dict

# ============================================================
# 全局配置
# ============================================================
NEWS_FILE = "news.txt"  # 新闻稿路径
CHUNK_SIZE = 4  # 每个块包含的句子数（3~5可调）
OVERLAP = 1  # 相邻块重叠的句子数（1~2可调）
TOP_K = 3  # 取Top-3相关块

# 大模型API配置（任务三、四使用）
# 支持OpenAI兼容格式，如Kimi、DeepSeek等
API_KEY = os.environ.get(
    "OPENAI_API_KEY", "your-api-key-here"
)  # 从环境变量读取或手动填写
API_BASE = os.environ.get(
    "OPENAI_BASE_URL", "https://api.moonshot.cn/v1"
)  # Kimi默认地址
MODEL_NAME = os.environ.get("MODEL_NAME", "moonshot-v1-8k")
USE_MOCK_API = API_KEY in ("", "your-api-key-here", None)  # 无Key时启用模拟模式

# ============================================================
# 任务一：无依赖文本切分
# ============================================================


def split_text(raw_text: str) -> List[Dict]:
    """
    任务一：无依赖文本切分

    处理逻辑：
      1. 按段落分割（\n\n）
      2. 对长段落，按。！？；切分成句子
      3. 相邻3~5个句子合并成一个块，块间重叠1~2个句子

    返回: [{"id": int, "text": str, "sentences": List[str]}]
    """
    # 步骤1：按段落分割
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]

    all_sentences = []

    for para in paragraphs:
        # 步骤2：按句子切分（支持。！？；）
        # 使用正则保留分隔符，避免丢失
        sentences = re.split(r"([。！？；])", para)

        # 合并分隔符和前一句
        merged = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i + 1] in "。！？；":
                merged.append(sentences[i] + sentences[i + 1])
                i += 2
            else:
                s = sentences[i].strip()
                if s:
                    merged.append(s)
                i += 1

        # 过滤空句子，清理空白
        for s in merged:
            s = s.strip()
            if len(s) > 1:  # 过滤单字/标点残留
                all_sentences.append(s)

    # 步骤3：滑动窗口合并成块
    chunks = []
    step = CHUNK_SIZE - OVERLAP  # 滑动步长

    idx = 0
    start = 0
    while start < len(all_sentences):
        end = min(start + CHUNK_SIZE, len(all_sentences))
        block_sentences = all_sentences[start:end]
        block_text = "".join(block_sentences)

        chunks.append({"id": idx, "text": block_text, "sentences": block_sentences})
        idx += 1
        start += step

    return chunks


def print_chunks(chunks: List[Dict]):
    """打印所有块，用于肉眼检查断句"""
    print("=" * 60)
    print(f"【任务一】文本切分结果：共生成 {len(chunks)} 个块")
    print(f"  配置：每块{CHUNK_SIZE}句，重叠{OVERLAP}句")
    print("=" * 60)

    for chunk in chunks:
        print(f"\n--- 块 #{chunk['id']} (含{len(chunk['sentences'])}句) ---")
        for j, sent in enumerate(chunk["sentences"], 1):
            print(f"  句{j}: {sent}")
        print(f"  [合并文本]: {chunk['text'][:120]}...")

    # 断句检查：查找可疑的短句或残留
    print("\n" + "=" * 60)
    print("【断句检查】")
    suspicious = []
    for chunk in chunks:
        for sent in chunk["sentences"]:
            # 如果句子过短（<5字）且不含标点，可能是断句错误
            if len(sent) < 5 and not re.search(r"[。！？；]$", sent):
                suspicious.append((chunk["id"], sent))

    if suspicious:
        print("  发现可疑短句（可能断句错误）：")
        for cid, sent in suspicious:
            print(f'    块{cid}: "{sent}"')
    else:
        print("  未发现明显断句错误 ✓")
    print("=" * 60)


# ============================================================
# 任务二：极简关键词搜索引擎
# ============================================================

# 停用词表（可扩展）
STOP_WORDS = set(
    [
        "的",
        "了",
        "吗",
        "呢",
        "吧",
        "啊",
        "哦",
        "嗯",
        "是",
        "在",
        "有",
        "和",
        "与",
        "或",
        "就",
        "都",
        "而",
        "及",
        "对",
        "为",
        "以",
        "从",
        "到",
        "向",
        "于",
        "被",
        "把",
        "让",
        "这",
        "那",
        "之",
        "个",
        "种",
        "些",
        "等",
        "该",
        "其",
        "此",
        "我",
        "你",
        "他",
        "她",
        "它",
        "我们",
        "你们",
        "他们",
        "什么",
        "怎么",
        "为什么",
        "如何",
        "谁",
        "哪",
        "哪里",
        "一个",
        "一下",
        "一种",
        "一直",
        "一样",
    ]
)


def preprocess_query(query: str) -> List[str]:
    """
    预处理用户问题：
      1. 去除停用词
      2. 提取关键词（简单按字/词切分，不依赖分词库）
    """
    # 去除标点
    query_clean = re.sub(r"[^\u4e00-\u9fff\w]", " ", query)

    # 简单切分：先尝试2-gram，再补充单字
    keywords = []
    words = query_clean.split()

    for w in words:
        w = w.strip()
        if not w or w in STOP_WORDS:
            continue
        if len(w) >= 2:
            keywords.append(w)
        elif len(w) == 1 and w not in STOP_WORDS:
            keywords.append(w)

    # 去重但保留顺序
    seen = set()
    unique_keywords = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique_keywords.append(k)

    return unique_keywords


def keyword_search(chunks: List[Dict], query: str) -> List[Tuple[Dict, int, Dict]]:
    """
    任务二：关键词匹配搜索

    返回: [(chunk, total_score, keyword_counts), ...] 按得分降序
    """
    keywords = preprocess_query(query)
    print(f"\n【任务二】关键词提取: {keywords}")

    results = []

    for chunk in chunks:
        text = chunk["text"]
        keyword_counts = {}
        total_score = 0

        for kw in keywords:
            # 统计关键词出现次数（简单子串匹配）
            count = text.count(kw)
            keyword_counts[kw] = count
            total_score += count

        results.append((chunk, total_score, keyword_counts))

    # 按得分降序排序
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def print_keyword_results(results: List[Tuple[Dict, int, Dict]], top_k: int = TOP_K):
    """打印关键词搜索结果"""
    print("=" * 60)
    print(f"【任务二】关键词搜索 Top-{top_k} 结果")
    print("=" * 60)

    for i, (chunk, score, counts) in enumerate(results[:top_k], 1):
        print(f"\n--- 排名 {i} | 块#{chunk['id']} | 得分: {score} ---")
        print(f"  关键词命中: {counts}")
        print(f"  原文: {chunk['text'][:200]}...")

    print("\n" + "=" * 60)


# ============================================================
# 任务三：手动封装AI问答函数
# ============================================================


def build_prompt(top_chunks: List[Dict], query: str) -> str:
    """手动拼接提示词"""
    prompt = (
        '请基于以下参考资料回答问题。如果参考资料里没有相关信息，请直接说"找不到"。\n'
    )

    for i, chunk in enumerate(top_chunks, 1):
        prompt += f"\n参考资料{i}：{chunk['text']}\n"

    prompt += f"\n问题：{query}\n"
    prompt += "答案："

    return prompt


def call_llm_api(prompt: str) -> str:
    """
    调用大模型API（OpenAI兼容格式）
    支持Kimi、DeepSeek等
    """
    if USE_MOCK_API:
        # 模拟模式：返回提示词本身，用于测试
        return (
            f"[模拟模式 - 未配置API Key]\n\n提示词预览（前500字）：\n{prompt[:500]}..."
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=API_KEY, base_url=API_BASE)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个基于参考资料回答问题的助手。请严格根据提供的参考资料回答，不要编造信息。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[API调用错误] {str(e)}"


def qa_with_keywords(chunks: List[Dict], query: str) -> str:
    """
    任务三：关键词检索 + AI问答
    """
    # 1. 关键词检索Top-3
    results = keyword_search(chunks, query)
    top_chunks = [r[0] for r in results[:TOP_K]]

    print_keyword_results(results, TOP_K)

    # 2. 构建提示词
    prompt = build_prompt(top_chunks, query)

    print("=" * 60)
    print("【任务三】构建的提示词（前800字）：")
    print("=" * 60)
    print(prompt[:800] + ("..." if len(prompt) > 800 else ""))
    print("=" * 60)

    # 3. 调用API
    print("\n正在调用大模型API...")
    answer = call_llm_api(prompt)

    return answer


# ============================================================
# 任务四：引入向量，替换关键词
# ============================================================


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    手写余弦相似度函数
    cos(θ) = (A·B) / (|A| * |B|)
    """
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def load_or_build_vectors(
    chunks: List[Dict], model_name: str = "all-MiniLM-L6-v2"
) -> Tuple[List, List]:
    """
    加载或构建文本块向量
    向量缓存到 vectors.pkl，避免重复编码
    """
    cache_file = "vectors.pkl"

    # 尝试加载缓存
    if os.path.exists(cache_file):
        print(f"\n发现向量缓存文件: {cache_file}，正在加载...")
        with open(cache_file, "rb") as f:
            cache = pickle.load(f)
            if cache.get("model") == model_name and len(cache["vectors"]) == len(
                chunks
            ):
                print("  缓存命中 ✓")
                return cache["vectors"], cache["chunks_text"]

    # 需要重新编码
    print(f"\n正在加载 sentence-transformers 模型: {model_name} ...")
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(model_name)
    except ImportError:
        print(
            "[错误] 未安装 sentence-transformers，请运行: pip install sentence-transformers"
        )
        raise

    print("  模型加载完成，正在编码文本块...")
    texts = [c["text"] for c in chunks]
    vectors = model.encode(texts, show_progress_bar=True)
    vectors = vectors.tolist()  # 转为Python列表

    # 保存缓存
    with open(cache_file, "wb") as f:
        pickle.dump({"model": model_name, "vectors": vectors, "chunks_text": texts}, f)
    print(f"  向量已缓存到 {cache_file}")

    return vectors, texts


def vector_search(
    chunks: List[Dict], query: str, vectors: List[List[float]], model
) -> List[Tuple[Dict, float]]:
    """
    任务四：向量相似度搜索

    返回: [(chunk, similarity), ...] 按相似度降序
    """
    print("\n【任务四】向量检索: 编码用户问题...")
    query_vector = model.encode([query])[0].tolist()

    results = []
    for chunk, vec in zip(chunks, vectors):
        sim = cosine_similarity(query_vector, vec)
        results.append((chunk, sim))

    # 按相似度降序排序
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def print_vector_results(results: List[Tuple[Dict, float]], top_k: int = TOP_K):
    """打印向量搜索结果"""
    print("=" * 60)
    print(f"【任务四】向量相似度搜索 Top-{top_k} 结果")
    print("=" * 60)

    for i, (chunk, sim) in enumerate(results[:top_k], 1):
        print(f"\n--- 排名 {i} | 块#{chunk['id']} | 相似度: {sim:.4f} ---")
        print(f"  原文: {chunk['text'][:200]}...")

    print("\n" + "=" * 60)


def qa_with_vectors(chunks: List[Dict], query: str) -> str:
    """
    任务四：向量检索 + AI问答
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")

    # 1. 加载/构建向量
    vectors, _ = load_or_build_vectors(chunks, "all-MiniLM-L6-v2")

    # 2. 向量检索Top-3
    results = vector_search(chunks, query, vectors, model)
    top_chunks = [r[0] for r in results[:TOP_K]]

    print_vector_results(results, TOP_K)

    # 3. 构建提示词
    prompt = build_prompt(top_chunks, query)

    print("=" * 60)
    print("【任务四】构建的提示词（前800字）：")
    print("=" * 60)
    print(prompt[:800] + ("..." if len(prompt) > 800 else ""))
    print("=" * 60)

    # 4. 调用API
    print("\n正在调用大模型API...")
    answer = call_llm_api(prompt)

    return answer


# ============================================================
# 完整RAG流程：命令行小工具
# ============================================================


def run_full_rag():
    """运行完整的RAG流程演示"""

    # 读取新闻稿
    if not os.path.exists(NEWS_FILE):
        print(f"错误：找不到文件 {NEWS_FILE}，请确保新闻稿已放置在当前目录。")
        return

    with open(NEWS_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("=" * 60)
    print("从零构建RAG原型 - 完整演示")
    print("=" * 60)
    print(f"新闻稿总字数: {len(raw_text)}")

    # ========== 任务一：文本切分 ==========
    chunks = split_text(raw_text)
    print_chunks(chunks)

    # 用户问题（可修改）
    query = "中国和美国在争议问题上的立场分别是什么？"
    print(f"\n【用户问题】{query}")

    # ========== 任务二+三：关键词检索 + AI问答 ==========
    print("\n" + "█" * 60)
    print("  方案A：关键词检索 → AI问答")
    print("█" * 60)
    answer_kw = qa_with_keywords(chunks, query)
    print(f"\n【关键词方案答案】\n{answer_kw}")

    # ========== 任务四：向量检索 + AI问答 ==========
    print("\n\n" + "█" * 60)
    print("  方案B：向量检索 → AI问答")
    print("█" * 60)

    try:
        answer_vec = qa_with_vectors(chunks, query)
        print(f"\n【向量方案答案】\n{answer_vec}")

        # 对比
        print("\n\n" + "=" * 60)
        print("【质量对比】")
        print("=" * 60)
        print("关键词方案：依赖字面匹配，可能遗漏语义相关但用词不同的内容。")
        print(
            "向量方案：  基于语义相似度，能捕获'仲裁'≈'裁决'、'美国'≈'美方'等语义关联。"
        )
        print("建议：实际应用中，向量检索通常召回更精准、答案质量更高。")
        print("=" * 60)

    except ImportError as e:
        print(f"\n[跳过任务四] {e}")
        print("请安装 sentence-transformers 后重试：pip install sentence-transformers")


def interactive_qa():
    """交互式问答小工具"""

    if not os.path.exists(NEWS_FILE):
        print(f"错误：找不到文件 {NEWS_FILE}")
        return

    with open(NEWS_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("\n正在初始化RAG系统...")
    chunks = split_text(raw_text)
    print(f"  文本已切分为 {len(chunks)} 个块")

    # 预加载向量（如果可用）
    vectors = None
    vec_model = None
    try:
        from sentence_transformers import SentenceTransformer

        vec_model = SentenceTransformer("all-MiniLM-L6-v2")
        vectors, _ = load_or_build_vectors(chunks)
        print("  向量模型已加载 ✓")
        use_vector = True
    except ImportError:
        print("  向量模型未安装，将使用关键词检索")
        use_vector = False

    print("\n" + "=" * 60)
    print("RAG问答小工具已启动（输入 'quit' 退出）")
    print("=" * 60)

    while True:
        query = input("\n你的问题: ").strip()
        if query.lower() in ("quit", "exit", "q", "退出"):
            print("再见！")
            break

        if not query:
            continue

        # 检索Top-3
        if use_vector:
            results = vector_search(chunks, query, vectors, vec_model)
            top_chunks = [r[0] for r in results[:TOP_K]]
            print(
                f"\n[向量检索] Top-3 相似度: {', '.join(f'{r[1]:.3f}' for r in results[:TOP_K])}"
            )
        else:
            results = keyword_search(chunks, query)
            top_chunks = [r[0] for r in results[:TOP_K]]
            print(
                f"\n[关键词检索] Top-3 得分: {', '.join(str(r[1]) for r in results[:TOP_K])}"
            )

        # 构建提示词并调用API
        prompt = build_prompt(top_chunks, query)
        answer = call_llm_api(prompt)

        print(f"\n>>> 答案: {answer}")


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_qa()
    else:
        run_full_rag()
