"""
新闻文本分块工具
功能：将新闻按段落和句子切分成有重叠的文本块
"""

import re


# ============ 第1部分：新闻分块工具（您已有的代码）============
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


def process_news_file(filename, chunk_size=4, overlap=1):
    """
    主处理函数
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
    for cid, chuck in all_chunks:
        print(f"\n[块 {cid}]")
        print(chunk)
        print("-" * 40)


# ============ 第2部分：检索模块（任务二）============


def main():
    """主函数"""
    # 请将你的新闻保存为 news.txt 放在同一目录下
    filename = "artic.txt"
    # 参数可调：
    # chunk_size: 每个块3-5个句子
    # overlap: 重叠1-2个句子
    process_news_file(filename, chunk_size=4, overlap=1)


if __name__ == "__main__":
    main()
