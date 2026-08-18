"""
新闻问答系统 - 整合检索与生成
功能：基于新闻分块检索，调用大模型API生成答案
"""

import os
import re

# ===== 新增：导入 requests 用于 API 调用 =====
import requests

# ===== 新增：导入 typing 用于类型提示 =====
from typing import List, Tuple
from dotenv import load_dotenv

load_dotenv()
deepseek_api_key = os.environ.get("APP_DEEPSEEK_API_KEY")
deepseek_url = os.environ.get("APP_DEEPSEEK_URL")
deepseek_model = os.environ.get("APP_DEEPSEEK_MODEL_NAME")

"""
    新闻文本分块工具 + AI问答系统
    功能：将新闻按段落和句子切分成有重叠的文本块，并支持基于检索的问答
"""


def _read_news_file(filename):
    """读取新闻文件"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 {filename}")
        return None


def _split_paragraphs(text):
    """按段落分割（双换行）"""
    # 按两个以上的换行分割
    sentences = re.split(r"\n\s*\n", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def _split_sentences(text):
    """
    按句子分割（。！？；）
    注意：保留了"华盛顿 —"这样的特殊情况不被切断
    """
    # 使用正则表达式，保留分隔符
    # (?<=[。！？；]) 表示在。！？；后面分割
    # 但要注意不分割英文缩写等
    sentences = re.split(r"(?<=[。！？；])\s*", text)
    # 过滤空句子
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def _create_chunks_perfect(sentences, chunk_size: int = 4, overlap: int = 1):
    """
    完美版：清晰、无bug、易懂
    思路：先切出所有完整的块，最后单独处理尾巴
    """

    # 如果句子太少，只生成一个块
    if len(sentences) <= chunk_size:
        return ["。".join(sentences)]

    chunks = []

    # 关键变量：当前取到的位置
    pos = 0

    # 第一步：先取所有"完整的块"
    # 条件：从当前位置开始，还能取到 chunk_size 句
    while pos + chunk_size <= len(sentences):
        # 取一块完整的
        end = pos + chunk_size
        chunk = sentences[pos:end]
        chunks.append("。".join(chunk))

        # 下一块从这里开始（重叠部分）
        pos = end - overlap

        # 如果下一块已经到末尾了，停止
        if pos >= len(sentences):
            return chunks

    # 第二步：处理剩下的尾巴
    # 循环结束后，pos 到末尾之间还剩下一些句子
    remaining = sentences[pos:]
    if len(remaining) >= 2:
        # 够2句，单独成块
        chunks.append("。".join(remaining))
    elif len(remaining) == 1 and chunks:
        # 只剩1句，塞进上一块（但要检查是否重复！）
        last_chunk = chunks[-1].split("。")
        if last_chunk != remaining[0]:
            last_chunk.append(remaining[0])
            chunks[-1] = "。".join(last_chunk)

    # 如果只剩1句但前面没有块，那就单独成块（但这种情况很少）
    elif len(remaining) == 1:
        chunks.append(remaining[0])
    return chunks


# ===== 新增：修改 process_news_file 函数，返回所有块列表（原函数保留打印功能） =====
def process_news_file(filename, chunk_size=4, overlap=1, return_chunks=False):
    """
    主处理函数
    参数 return_chunks: 如果为 True，返回所有文本块列表；否则只打印
    """
    # 读取文件
    text = _read_news_file(filename)
    # _split_sentences(text)

    print("=*=" * 20)
    print(f"处理文件{filename}")
    print(f"块大小: {chunk_size} 句, 重叠: {overlap} 句")
    print(f"处理文件{filename}")
    print()

    # 2. 按段落分割
    paragraphs = _split_paragraphs(text)
    print(f"共找到 {len(paragraphs)} 个段落")
    print()

    # 3. 对每个段落处理

    all_chunks = []
    chunk_id = 1
    for para_idx, paragraph in enumerate(paragraphs, 1):
        print(f"--------------段落(索引) {para_idx} ---------------------")
        print(f"原始内容: {paragraph[:100]}...")
        print()

        # 4. 按句子分割
        sentences = _split_sentences(paragraph)
        print(f"检测到:{len(sentences)}个句子")
        for i, sent in enumerate(sentences, 1):
            print(f"    句子:{i}: {sent}")
        print()

        # 5. 生成块
        if len(sentences) > 0:
            chunks = _create_chunks_perfect(sentences, chunk_size, overlap)
            print("    块:", chunks)
            print(f"    生成 {len(chunks)} 个块:")
            for chunk in chunks:
                # 统计这个块包含的句子数
                sent_count = len(_split_sentences(chunk))
                print(f"    test_块:{chunk_id}， 包含句子数：{sent_count}")
                print(f"    {chunk}")
                print()
                all_chunks.append((chunk_id, chunk))
                chunk_id += 1

        print("=*=" * 20)
        print()

    # 6. 汇总输出
    print("=" * 60)
    print("所有块汇总:")
    print("=" * 60)
    for cid, chunk in all_chunks:
        print(f"\n[块 {cid}]")
        print(chunk)
        print("-" * 40)

    # ===== 新增：根据参数返回块列表 =====
    if return_chunks:
        # 只返回文本内容，不返回ID
        return [chunk for _, chunk in all_chunks]
    return None


# ===== 新增：检索模块（任务二） =====
def retrieve_top_k(
    chunks: List[str], query: str, k: int = 3
) -> List[Tuple[str, float]]:
    """
    检索Top-K相关块（基于关键词匹配的简单实现）
    参数：
        chunks: 所有文本块列表
        query: 用户问题
        k: 返回的块数量
    返回：[(块内容, 相关度得分), ...]
    """
    # 简单关键词匹配检索
    query_words = set(query.lower().split())

    scores = []
    for chunk in chunks:
        # 计算关键词覆盖率
        chunk_words = set(chunk.lower().split())
        overlap = len(query_words & chunk_words)
        # 加上长度归一化，避免长文本得分过高
        score = overlap / (len(chunk.split()) ** 0.5 + 1)
        scores.append((chunk, score))

    # 按得分排序，返回Top-K
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:k]


# ===== 新增：AI问答模块 =====
def call_llm_api(prompt: str, api_config: dict) -> str:
    """
    调用大模型API
    请根据您第1周使用的API修改此函数
    参数：
        prompt: 完整的提示词
        api_config: API配置字典，包含 api_key, api_url, model
    返回：模型生成的答案
    """
    # 示例：使用OpenAI API（请替换为您的实际配置）
    api_key = api_config.get("api_key", "your-api-key")
    api_url = api_config.get("api_url", "https://api.openai.com/v1/chat/completions")
    model = api_config.get("model", "gpt-3.5-turbo")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个基于新闻内容回答问题的助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"API调用失败: {str(e)}"


# ===== 新增：构建提示词函数 =====
def build_prompt(query: str, chunks: List[Tuple[str, float]]) -> str:
    """
    构建问答提示词
    参数：
        query: 用户问题
        chunks: 检索到的Top-K块列表 [(块内容, 得分), ...]
    返回：完整的提示词字符串
    """
    prompt = (
        '请基于以下参考资料回答问题。如果参考资料里没有相关信息，请直接说"找不到"。\n\n'
    )

    for i, (chunk, score) in enumerate(chunks, 1):
        prompt += f"参考资料{i}：{chunk}\n\n"

    prompt += f"问题：{query}\n"
    prompt += "答案："

    return prompt


# ===== 新增：完整的问答流程 =====
def answer_question(
    query: str, chunks: List[str], api_config: dict, top_k: int = 3
) -> str:
    """
    完整的问答流程：
    1. 检索Top-K相关块
    2. 构建提示词
    3. 调用大模型生成答案
    参数：
        query: 用户问题
        chunks: 所有文本块列表
        api_config: API配置
        top_k: 检索返回的块数量
    返回：最终答案字符串
    """
    print(f"\n{'='*60}")
    print(f"问题：{query}")
    print(f"{'='*60}\n")

    # 1. 检索
    print("正在检索相关块...")
    top_chunks = retrieve_top_k(chunks, query, top_k)

    print(f"找到 {len(top_chunks)} 个相关块：")
    for i, (chunk, score) in enumerate(top_chunks, 1):
        print(f"\n  块{i} (相关度: {score:.3f})")
        print(f"  {chunk[:100]}...")

    # 2. 构建提示词
    print("\n正在构建提示词...")
    prompt = build_prompt(query, top_chunks)
    print(f"\n提示词预览：\n{prompt[:200]}...\n")

    # 3. 调用API
    print("正在调用大模型API...")
    answer = call_llm_api(prompt, api_config)

    print(f"\n{'='*60}")
    print("最终答案：")
    print(f"{'='*60}")
    print(answer)
    print(f"{'='*60}\n")

    return answer


# ===== 新增：命令行交互工具 =====
def run_qa_system(filename="artic.txt", api_config=None):
    """
    运行命令行问答工具
    参数：
        filename: 新闻文件名
        api_config: API配置字典
    """
    if api_config is None:
        api_config = {
            "api_key": deepseek_api_key,  # 请替换为您的API Key
            "api_url": deepseek_url,
            "model": deepseek_model,
        }

    print("=" * 60)
    print("新闻问答系统")
    print("=" * 60)

    # 加载新闻
    print(f"\n正在加载新闻文件：{filename}")
    # ===== 修改：调用 process_news_file 并传入 return_chunks=True =====
    chunks = process_news_file(filename, chunk_size=4, overlap=1, return_chunks=True)

    if not chunks:
        print("错误：无法加载新闻文件或文件为空")
        return

    print(f"成功加载 {len(chunks)} 个文本块\n")

    # 交互问答
    while True:
        print("\n" + "-" * 60)
        query = input("请输入您的问题（输入 'quit' 退出）：").strip()

        if query.lower() in ["quit", "exit", "q"]:
            print("感谢使用，再见！")
            break

        if not query:
            print("问题不能为空，请重新输入")
            continue

        # 回答问题
        answer_question(query, chunks, api_config, top_k=3)


# ===== 修改：main 函数，可以选择运行原功能或问答系统 =====
def main():
    """主函数"""
    # 请将你的新闻保存为 news.txt 放在同一目录下
    filename = "artic.txt"

    # ===== 新增：选择运行模式 =====
    print("请选择运行模式：")
    print("1. 仅分块（原功能）")
    print("2. 分块 + 问答系统（新功能）")
    choice = input("请输入选项（1或2）：").strip()

    if choice == "2":
        # 问答模式
        api_config = {
            "api_key": deepseek_api_key,  # 请替换为您的API Key
            "api_url": deepseek_url,
            "model": deepseek_model,
        }
        run_qa_system(filename, api_config)
    else:
        # 原分块模式
        process_news_file(filename, chunk_size=4, overlap=1, return_chunks=False)


if __name__ == "__main__":
    main()
