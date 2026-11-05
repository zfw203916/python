#!/usr/bin/env python3
# clean_dataset.py
# 用法：uv run python clean_dataset.py dataset_v3.json
# 输出：
#   dataset_v3_cleaned.json   清洗后数据
#   dataset_v3_removed.json   被删除的数据（带删除原因，方便人工复核）
#   dataset_v3_cleaned.xlsx   （可选）方便用 Excel 看
#   dataset_v3_removed.xlsx   （可选）方便用 Excel 复核

import json
import re
import sys
from collections import Counter
from pathlib import Path

if len(sys.argv) < 2:
    print("用法: python clean_dataset.py <dataset.json>")
    sys.exit(1)

src = Path(sys.argv[1]).expanduser().resolve()
if not src.exists():
    print(f"文件不存在: {src}")
    sys.exit(1)

out_cleaned = src.with_name(src.stem + "_cleaned.json")
out_removed = src.with_name(src.stem + "_removed.json")
out_cleaned_xlsx = src.with_name(src.stem + "_cleaned.xlsx")
out_removed_xlsx = src.with_name(src.stem + "_removed.xlsx")

with src.open("r", encoding="utf-8") as f:
    data = json.load(f)

original_n = len(data)

# ==================== 配置（可调） ====================
KEEP_GREETINGS = False   # True = 保留"你好"/"hi"等纯问候语；False = 删除

GREETINGS = {"你好", "您好", "hi", "hello", "哈喽", "在吗", "在么", "在不在"}

AD_KEYWORDS = [
    # 联系方式 / 引流
    "telegram", "whatsapp", "tg号", "飞机", "飞鸡", "飞叽", "非叽",
    # 业务特征
    "工作室", "移分", "套利", "黑科技", "漏洞", "包赢", "日赚", "月入",
    "财富自由", "狗庄", "薅羊毛", "带躺", "上岸", "内部人员",
    "包输", "收额度", "运营站", "彩票量大", "马来西亚",
    "日入几万", "月入20w", "日赚10w", "点点鼠标", "无任何风险",
    "诚信合作", "一路长虹", "大展拳脚", "联系我", "私聊",
]

# ==================== 工具函数 ====================
def norm(s):
    if not isinstance(s, str):
        return ""
    return re.sub(r"\s+", " ", s.strip())

def norm_key(s):
    """去重用：去空白 + 小写"""
    return re.sub(r"\s+", "", norm(s)).lower()

def is_url_only(s):
    return bool(re.fullmatch(r"https?://\S+", s, re.I))

def is_pure_digits(s):
    return bool(re.fullmatch(r"\d+", s))

def is_account_like(s):
    """纯字母数字空格下划线中划线点，必须含字母，不含中文。
    覆盖 ppp999 / meng zu yi188 / aa13610533400 / 2026abc 这类账号。"""
    if not re.fullmatch(r"[A-Za-z0-9_\-. ]+", s):
        return False
    return bool(re.search(r"[A-Za-z]", s))

def is_single_char(s):
    return len(s) <= 1

def is_punct_only(s):
    """所有非表情码字符都不是字母/数字/中文"""
    s2 = re.sub(r"\[\[[^\]]+\]\]", "", s).strip()  # 去掉 [[joy]] 这种表情码
    if not s2:
        return True
    return all(not ch.isalnum() for ch in s2)

def is_ad(s):
    low = s.lower()
    return any(k.lower() in low for k in AD_KEYWORDS)

def is_greeting(s):
    return norm_key(s) in GREETINGS

# ==================== Level 0：无效过滤 ====================
def check_invalid(item):
    q = norm(item.get("query", ""))
    if not q:                       return "empty_query"
    if is_url_only(q):              return "url_only"
    if is_pure_digits(q):           return "pure_digits"
    if is_account_like(q):          return "account_like"
    if is_single_char(q):           return "single_char"
    if is_punct_only(q):            return "punct_only"
    if is_ad(q):                    return "ad"
    if not KEEP_GREETINGS and is_greeting(q): return "greeting_only"
    return None

kept = []
removed = []
for item in data:
    reason = check_invalid(item)
    if reason:
        r = dict(item); r["_remove_reason"] = reason
        removed.append(r)
    else:
        kept.append(item)

invalid_n = len(removed)
reason_counter = Counter(r["_remove_reason"] for r in removed)

# ==================== Level 1-4：去重 ====================
def drop_duplicates(items, key_fn, reason):
    seen = set()
    kept_, dropped_ = [], []
    for item in items:
        k = key_fn(item)
        if k is not None and k in seen:
            r = dict(item); r["_remove_reason"] = reason
            dropped_.append(r)
            continue
        if k is not None:
            seen.add(k)
        kept_.append(item)
    return kept_, dropped_

# L1: 完全重复
def full_key(it):
    return json.dumps(it, sort_keys=True, ensure_ascii=False)

kept1, removed_full = drop_duplicates(kept, full_key, "full_duplicate")

# L2: id 重复
def id_key(it):
    return it.get("id") or None

kept2, removed_id = drop_duplicates(kept1, id_key, "duplicate_id")

# L3: original_id 重复
def oid_key(it):
    return it.get("original_id") or None

kept3, removed_oid = drop_duplicates(kept2, oid_key, "duplicate_original_id")

# L4: 业务重复 = normalize(query) + expected_intent
def biz_key(it):
    q = norm_key(it.get("query", ""))
    intent = norm(it.get("expected_intent", ""))
    if not q:
        return None
    return (q, intent)

kept4, removed_biz = drop_duplicates(kept3, biz_key, "business_duplicate")

removed_all = removed + removed_full + removed_id + removed_oid + removed_biz

# ==================== 输出 ====================
with out_cleaned.open("w", encoding="utf-8") as f:
    json.dump(kept4, f, ensure_ascii=False, indent=2)

with out_removed.open("w", encoding="utf-8") as f:
    json.dump(removed_all, f, ensure_ascii=False, indent=2)

xlsx_note = ""
try:
    import pandas as pd
    pd.DataFrame(kept4).to_excel(out_cleaned_xlsx, index=False)
    pd.DataFrame(removed_all).to_excel(out_removed_xlsx, index=False)
except Exception as e:
    xlsx_note = f"（xlsx 未生成：{e}，不影响 JSON 输出）"

# ==================== 统计 ====================
print("=" * 64)
print(f"原始条数：{original_n}")
print("-" * 64)
print(f"无效过滤合计：{invalid_n}")
for k, v in reason_counter.most_common():
    print(f"   {k:<12} {v}")
print("-" * 64)
print("去重：")
print(f"   完全重复              {len(removed_full)}")
print(f"   id 重复               {len(removed_id)}")
print(f"   original_id 重复      {len(removed_oid)}")
print(f"   业务重复(query+intent) {len(removed_biz)}")
print("-" * 64)
print(f"最终保留：{len(kept4)}")
print(f"总删除：  {len(removed_all)}")
print("=" * 64)
print("输出：")
print(f"  {out_cleaned}")
print(f"  {out_removed}")
if not xlsx_note:
    print(f"  {out_cleaned_xlsx}")
    print(f"  {out_removed_xlsx}")
else:
    print(f"  {xlsx_note}")