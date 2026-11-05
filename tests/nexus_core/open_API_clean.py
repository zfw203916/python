# -*- coding: utf-8 -*-
# pip install pandas openpyxl openai tqdm
import os
import re
import json
import shutil
import hashlib
import unicodedata
from collections import defaultdict
import pandas as pd
from openpyxl import load_workbook
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============ 配置 ============
SRC            = "selete_data/49CP_(2026-08-09)_客服稽核报告_正式版.xlsx"
SRC_SHEET      = "統計"

TEMPLATE       = "selete_data/knowledge-import.xlsx"
TPL_MAIN_SHEET = "知识条目"
TPL_DESC_SHEET = "填写说明"

OUT_XLSX       = "selete_data/knowledge-import-output.xlsx"
OUT_TSV        = "selete_data/knowledge-import-output.tsv"

MODEL          = "gpt-4o-mini"
MAX_INTENT     = 119

MERGE_AFTER_NORMALIZE = True
BATCH_SIZE = 20          # 过滤时每批处理的条数
MAX_WORKERS = 5          # 并发线程数（建议 5-10，太高会被 API 限流）

MSG_PAT = re.compile(r"^(客服|访客)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}):$")
SYS_PAT = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

# ============ 表头归一化 ============
def normalize_col(name: str) -> str:
    s = "" if name is None else str(name)
    s = s.replace("\u3000", " ")
    s = re.sub(r"\s+", "", s)
    s = s.replace("（", "(").replace("）", ")")
    s = s.replace("：", ":").replace("，", ",")
    s = unicodedata.normalize("NFKC", s)
    return s.strip()

def load_template_columns(template_path: str, sheet_name: str):
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"找不到模板文件：{template_path}")
    head = pd.read_excel(template_path, sheet_name=sheet_name, nrows=0)
    raw_cols = [str(c) for c in head.columns]
    norm_to_raw = {normalize_col(c): c for c in raw_cols}
    print(f"模板路径：{template_path}")
    print(f"模板字段（{len(raw_cols)} 个）：{raw_cols}")
    return raw_cols, norm_to_raw

# ============ 解析对话 ============
def split_lines(text: str):
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    out = []
    for p in text.split("\n"):
        out.extend(p.split("<br>"))
    return out

def parse_messages(text: str):
    msgs, cur = [], None
    for line in split_lines(text):
        s = line.strip()
        if not s:
            continue
        m = MSG_PAT.match(s)
        if m:
            if cur:
                msgs.append(cur)
            cur = {"role": m.group(1), "time": m.group(2), "content": ""}
            continue
        if SYS_PAT.match(s):
            if cur:
                msgs.append(cur)
                cur = None
            continue
        if cur is not None:
            cur["content"] = (cur["content"] + "<br>" + s) if cur["content"] else s
    if cur:
        msgs.append(cur)
    return msgs

# ============ 噪音过滤 ============
NOISE_EXACT = {
    "好的", "收到，谢谢", "忘了截图", "嗯", "哦", "啊", "在吗", "你好",
    "在", "是的", "对的", "行", "可以", "谢谢",
}

def is_noise_question(q: str) -> bool:
    q = q.strip()
    if not q:
        return True
    if q in NOISE_EXACT:
        return True
    if q.startswith("http://") or q.startswith("https://"):
        return True
    if re.fullmatch(r"[A-Za-z0-9_.\-@]+", q):
        return True
    if not re.search(r"[\w\u4e00-\u9fff]", q):
        return True
    if len(q) >= 2 and len(set(q)) == 1:
        return True
    return False

# ============ 分类映射 ============
def map_category(tag: str) -> str:
    t = str(tag)
    if "充值" in t:
        return "充值"
    if "提款" in t:
        return "提款"
    if any(k in t for k in ["钱包", "账户", "帳號", "帐号", "密码", "登录",
                             "个人信息", "银行卡", "冻结", "余额"]):
        return "账户"
    return "其他"

# ============ intent 拼接 + 强制截断 ============
def pick_core_answer(answer: str) -> str:
    parts = [p.strip() for p in answer.split("<br>") if p.strip()]
    for p in parts:
        if re.search(r"\d+(\.\d+)?[%元天个分]|不能|可以|需要|最高|最低|规则|申请|切换|取消|请提供|请使用", p):
            return p
    return parts[0] if parts else ""

def build_intent(q: str, a: str, max_len: int = None):
    if max_len is None:
        max_len = MAX_INTENT
    core = pick_core_answer(a)
    sep = " | "
    q, core = q.strip(), core.strip()
    if len(q) + len(sep) + len(core) <= max_len:
        return q + sep + core, False
    remain = max_len - len(q) - len(sep)
    if remain > 0:
        return q + sep + core[:remain], False
    return q[:max_len], True

# ============ LLM 客户端 ============
def get_client():
    api_key = "sk-proj--EA"
    if not api_key:
        print("[WARN] 未设置 OPENAI_API_KEY，跳过所有 LLM 步骤（规范化 + 过滤）。")
        return None
    base_url = os.environ.get("OPENAI_BASE_URL") or None
    if base_url:
        print(f"[INFO] 使用自定义 base_url：{base_url}")
    else:
        print("[INFO] 使用 OpenAI 官方 base_url")
    # 加超时设置，防止无限挂起
    return OpenAI(api_key=api_key, base_url=base_url, timeout=60.0, max_retries=2)

# ============ 问法规范化（并发 + 进度条） ============
def normalize_questions(candidates, conversations, client):
    if client is None:
        print("[WARN] 无 LLM 客户端，跳过问法规范化。")
        return candidates

    by_row = defaultdict(list)
    for i, c in enumerate(candidates):
        by_row[c["row"]].append(i)

    def process_row(row_no, indices):
        conv_text = conversations.get(row_no, "")
        if not conv_text:
            return []
        payload = [
            {"index": k, "question": candidates[i]["question"], "answer": candidates[i]["answer"]}
            for k, i in enumerate(indices)
        ]
        prompt = f"""你是客服知识库助手。下面是一个完整的客服会话，以及从中提取的若干条「访客问法 + 客服回答」。

请为每条问法判断：它是否是一个「自包含的完整问法」——即脱离上下文，其他用户也能直接看懂在问什么。

规则：
1. 如果问法本身已完整（有主语/对象/动作），原样返回，complete=true。
2. 如果是碎片化追问（如"能申请多少""不是七天吗""怎么弄"），结合会话上文补全为完整问句，complete=true。
3. 补全时只能使用会话中出现过的信息：
   - 上文提到"周彩"，"能申请多少" → "周彩金能申请多少"
   - 上文提到"注册满七天"，"不是七天吗" → "周彩金注册满七天就能申请吗"
   - 不得添加会话里没有的内容，不得改变原意
4. 如果信息不足以补全，原样返回，complete=false。
5. 不要改写已经完整的问法，不要润色，不要加礼貌用语。

返回 JSON：{{"results": [{{"index": 0, "normalized": "...", "complete": true}}, ...]}}
index 必须与输入一致，results 数量必须等于输入数量。

会话全文：
{conv_text}

待处理问法：
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            data = json.loads(resp.choices[0].message.content)
            results = []
            for r in data.get("results", []):
                k = r.get("index")
                if not isinstance(k, int) or k < 0 or k >= len(indices):
                    continue
                i = indices[k]
                norm = (r.get("normalized") or "").strip()
                complete = bool(r.get("complete", True))
                results.append((i, norm, complete))
            return results
        except Exception as e:
            # 失败时不中断，保留原文
            return []

    # 并发执行
    tasks = [(row, idxs) for row, idxs in by_row.items() if conversations.get(row)]
    print(f"开始问法规范化，共 {len(tasks)} 个会话需处理...")
    
    total_norm = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_row, r, i): r for r, i in tasks}
        for future in tqdm(as_completed(futures), total=len(tasks), desc="规范化进度"):
            res = future.result()
            for i, norm, complete in res:
                if norm and norm != candidates[i]["question"]:
                    candidates[i]["original_question"] = candidates[i]["question"]
                    candidates[i]["question"] = norm
                    candidates[i]["q_complete"] = complete
                    total_norm += 1
                else:
                    candidates[i]["q_complete"] = complete

    print(f"问法规范化：{total_norm} 条被补全")
    return candidates

# ============ 规范化后合并 ============
def merge_after_normalize(candidates):
    merged = {}
    order = []
    for c in candidates:
        key = c["question"]
        if key not in merged:
            c["original_variants"] = [c.get("original_question", c["question"])]
            merged[key] = c
            order.append(key)
        else:
            prev = merged[key]
            orig = c.get("original_question", c["question"])
            if orig not in prev["original_variants"]:
                prev["original_variants"].append(orig)
            if len(c["answer"]) > len(prev["answer"]):
                prev["answer"] = c["answer"]
    result = [merged[k] for k in order]
    print(f"规范化后合并：{len(candidates)} → {len(result)} 条")
    return result

# ============ LLM 过滤（分批 + 并发） ============
def call_llm_filter(candidates, client):
    if not candidates:
        return []
    if client is None:
        print("[WARN] 无 LLM 客户端，跳过过滤，保留全部候选。")
        return list(range(len(candidates)))

    def process_batch(batch_data, start_idx):
        payload = [{"index": k, "question": c["question"], "answer": c["answer"], "tag": c["tag"]} for k, c in enumerate(batch_data)]
        prompt = f"""你是客服知识库整理助手。下面是脚本从客服对话原文中提取的「访客问法 + 客服回答」候选列表，问法已做上下文补全。

你的唯一任务是：判断每条候选是否适合作为客服知识条目，返回有效索引。
不要生成、改写、拼接任何字段；不要输出标题、问法、正文、intent、JSON；这些由脚本按模板生成。

判定原则（只能依据候选里的 question / answer 原文，不得脑补、不得编造、不得改写）：
排除：
- 纯广告、活动推送、欢迎语、纯链接、纯符号、纯表情符号、重复单个字的(如：哦哦哦等）
- 空单、无实质问题（打招呼、测试、乱码、表情、纯账号、纯数字）
- 回答为空
- 与业务无关的闲聊
- 问法补全后仍无法独立理解（语义不明）

保留：
- 有明确问题 + 客服给出可复用的解答
- 标准引导话术（如“请提供截图/会员账号”）也保留，因为真实用户会这么问
- 回答含个人查询但夹带通用规则的，保留
- 回答相同但问法不同的，全部保留，不得合并
- 问法意思相近但字面不同的（近义变体），全部保留，不得因相似而排除

返回 JSON：{{"valid_indices": [0,1,2,...]}}，只返回有效索引，不要返回其他内容。

候选列表：
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            data = json.loads(resp.choices[0].message.content)
            idxs = data.get("valid_indices", [])
            valid = []
            for i in idxs:
                try:
                    k = int(i)
                    if 0 <= k < len(batch_data):
                        valid.append(start_idx + k)
                except:
                    pass
            return valid
        except Exception as e:
            # 失败时兜底全留
            return [start_idx + k for k in range(len(batch_data))]

    # 切分批次
    batches = []
    for i in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[i:i+BATCH_SIZE]
        batches.append((batch, i))
        
    print(f"开始 LLM 过滤，共 {len(candidates)} 条，分 {len(batches)} 批...")
    all_valid = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_batch, b, start): start for b, start in batches}
        for future in tqdm(as_completed(futures), total=len(batches), desc="过滤进度"):
            all_valid.extend(future.result())
            
    return sorted(set(all_valid))

# ============ 主流程 ============
def main():
    if not os.path.exists(SRC):
        raise FileNotFoundError(f"找不到源文件：{SRC}")

    tpl_raw_cols, tpl_norm_to_raw = load_template_columns(TEMPLATE, TPL_MAIN_SHEET)
    client = get_client()

    df = pd.read_excel(SRC, sheet_name=SRC_SHEET)
    conversations = {int(r["编号"]): str(r["对话内容"]) for _, r in df.iterrows()}

    # 1) 提取
    candidates = []
    for _, r in df.iterrows():
        row_no = r["编号"]
        visitor_id = str(r["访客ID"])
        tag = str(r["对话标签"]) if pd.notna(r["对话标签"]) else "其他"
        msgs = parse_messages(r["对话内容"])

        for i, m in enumerate(msgs):
            if m["role"] != "访客": continue
            q = m["content"].strip()
            if is_noise_question(q): continue
            
            answers = []
            for j in range(i + 1, len(msgs)):
                if msgs[j]["role"] == "访客": break
                if msgs[j]["role"] == "客服":
                    txt = msgs[j]["content"].strip()
                    if txt: answers.append(txt)
            
            if not answers: continue
            answer_text = "<br>".join(answers)
            if not answer_text.strip(): continue
            
            candidates.append({
                "row": int(row_no),
                "visitor_id": visitor_id,
                "tag": tag,
                "question": q,
                "answer": answer_text,
            })

    print(f"提取候选：{len(candidates)} 条")

    # 2) 去重
    seen, uniq = set(), []
    for c in candidates:
        if c["question"] in seen: continue
        seen.add(c["question"])
        uniq.append(c)
    print(f"原文去重后：{len(uniq)} 条")

    # 3) 规范化
    uniq = normalize_questions(uniq, conversations, client)

    # 4) 合并
    if MERGE_AFTER_NORMALIZE:
        uniq = merge_after_normalize(uniq)

    # 5) 过滤
    valid_idx = call_llm_filter(uniq, client)
    valid = [uniq[i] for i in valid_idx]
    print(f"LLM 过滤后：{len(valid)} 条")

    # 6) 生成记录
    rows = []
    for seq, c in enumerate(valid, start=1):
        q, a = c["question"], c["answer"]
        intent, need_review = build_intent(q, a)
        answer_hash = hashlib.md5(a.encode("utf-8")).hexdigest()[:8]

        variants = c.get("original_variants") or [c.get("original_question", q)]
        q_lines = [q] + [v for v in variants if v != q]
        q_field = "\n".join(q_lines)

        other = {
            "intent": intent,
            "source_file": os.path.basename(SRC),
            "row": c["row"],
            "visitor_id": c["visitor_id"],
            "original_text": c.get("original_question", q),
            "normalized_text": q,
            "answer_group": answer_hash,
        }
        if len(q_lines) > 1: other["original_variants"] = q_lines[1:]
        if need_review: other["needs_review"] = True
        if c.get("q_complete") is False: other["q_complete"] = False

        rec = {
            "条目标识": f"auto_49cp_{c['row']}_{seq}",
            "类型": "knowledge",
            "标题": q,
            "治理分类": map_category(c["tag"]),
            "回答方式": "fixed",
            "风险等级": "low",
            "热门": "否",
            "正文(简体)": a,
            "繁体覆盖": "",
            "问法(每行一条)": q_field,
            "排除词(每行一条)": "",
            "适用范围": "不限",
            "生效日期": "",
            "失效日期": "",
            "依据": f"{os.path.basename(SRC)}|编号={c['row']}|访客ID={c['visitor_id']}",
            "其他字段(JSON)": json.dumps(other, ensure_ascii=False),
        }

        aligned = {raw_col: rec.get(normalize_col(raw_col), "") for raw_col in tpl_raw_cols}
        rows.append(aligned)

    # 7) 写入
    shutil.copyfile(TEMPLATE, OUT_XLSX)
    wb = load_workbook(OUT_XLSX)
    ws = wb[TPL_MAIN_SHEET]
    if ws.max_row > 1: ws.delete_rows(2, ws.max_row - 1)
    for r_idx, row in enumerate(rows, start=2):
        for c_idx, raw_col in enumerate(tpl_raw_cols, start=1):
            ws.cell(row=r_idx, column=c_idx, value=row.get(raw_col, ""))
    wb.save(OUT_XLSX)
    print(f"已写入模板副本：{OUT_XLSX}")

    # 8) 输出
    out_df = pd.DataFrame(rows, columns=tpl_raw_cols)
    out_df.to_csv(OUT_TSV, index=False, sep="\t", encoding="utf-8-sig")
    print(f"已生成 TSV：{OUT_TSV}")

    # 9) 校验
    json_col = tpl_norm_to_raw.get("其他字段(JSON)")
    if json_col:
        bad = []
        for it in rows:
            try:
                if len(json.loads(it.get(json_col, "")).get("intent", "")) > MAX_INTENT:
                    bad.append(it)
            except: pass
        if bad: print(f"[ERROR] 仍有 {len(bad)} 条 intent 超长。")
        else: print(f"全部 intent 均 ≤ {MAX_INTENT} 字符。")

if __name__ == "__main__":
    main()