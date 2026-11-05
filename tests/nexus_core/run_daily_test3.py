import json
import requests
import csv
import time
from datetime import datetime
import sys
from openai import OpenAI
sys.stdout.reconfigure(line_buffering=True)
API_URL="https://admin.pubuli.com/api/v1/workbench/reply-traces/try-compose"
COOKIE_VALUE="nexus_refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX3V1aWQiOiJmOWU3NGEzZS02MDQxLTQ3MDItYjM2Mi1iYzAxM2I0ZGVhNmEiLCJqdGkiOiJmOGZlMzFhMy04NjJmLTRmNGMtYTMwNi1mODA1NmNiMzQ1ZDUiLCJleHAiOjE3OTM4ODAwMzMuNDc4ODM3LCJzdWIiOiIyMjIzNDE1OTk0MjA5MDEzNzYwIn0.iECFErck4rrELxRNdRaUPVneMjjSlcY93AUq8U7kvEw"
Authorization_Value="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX3V1aWQiOiJmOWU3NGEzZS02MDQxLTQ3MDItYjM2Mi1iYzAxM2I0ZGVhNmEiLCJqdGkiOiJhOTdmNjYzYi02ODBmLTQyZjUtYjgwYi03NmM0YjliNDIzY2YiLCJleHAiOjE3OTMzNjE2MzMuNDc1NDMzLCJzdWIiOiIyMjIzNDE1OTk0MjA5MDEzNzYwIn0.fc-PhqfaHKV2HG_lAc4-ESf0yiPzBjRMv55WGsv2efw"
HEADERS={
    "Content-Type": "application/json",
    "Cookie":COOKIE_VALUE,
    "Authorization":Authorization_Value,
}
DATASET_FILE="dataset_v1_test.json"

OPENAI_API_KEY = "sk-proj--EA"  
OPENAI_MODEL   = "gpt-4o-mini"   # ★ gpt-4o-mini "gpt-4o" / "gpt-5.2"
OPENAI_TIMEOUT = 30.0
OPENAI_RETRIES = 2

# 初始化全局 OpenAI 客户端（只建一次，复用连接）
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=OPENAI_TIMEOUT,        # 单次请求 30 秒超时
    max_retries=OPENAI_RETRIES,       # 429/5xx 自动重试 2 次
)

# judge_hallucination —— 完全交给 OpenAI
def judge_hallucination(query: str, expected_intent: str, reply_text: str, is_kb_hit):
    """
    完全依赖 OpenAI 判定未命中知识库时 AI 回复是否存在幻觉。
    返回："有" / "无" / "未知"
      - 命中知识库 / 空回复：业务前置条件，直接返回"无"（无本地规则兜底）
      - 其余情况：一律走 OpenAI
      - 任何异常（网络/超时/限流/JSON 非法/字段异常）：返回"未知"，绝不伪装成"无"
    """
    # ---- 前置短路（业务条件，非规则兜底）----
    # is_kb_hit 是否知识库。
    if is_kb_hit == "是":
        return "无"
    if not reply_text:
        return "无"
    
    prompt = f"""
        用户问题：{query}
        标准意图：{expected_intent}
        AI回复: {reply_text}
       判定标准：
        - 若 AI 回复与用户问题/标准意图明显无关（例：问提款却答投注/游戏/充值），判为 "有"。
        - 若 AI 回复切题、业务逻辑一致，判为 "无"。
        - 只返回 JSON:{{"hallucination": "有"}} 或 {{"hallucination": "无"}}，不要附加任何其他文字。"""
            
    try:
        completion = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个只输出JSON的裁判,不闲聊。"},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.0,                            # 判定任务用 0，结果最稳定
            response_format={"type": "json_object"},    # 强制输出合法 JSON
        )
        raw = completion.choices[0].message.content 
        data = json.loads(raw)
        verdict = data.get("hallucination","")
        if verdict == "有":
            return "有"
        if verdict == "无":
            return "无"
        # 字段缺失/取值异常为:未知
        print(f"  ⚠️ LLM 返回值异常：{raw[:80]}...")
        return "未知"
    except Exception as e:
        # 网络/超时/限流/JSON 解析失败 ,全部视为"未知"
        print(f"  ⚠️ LLM 判定失败：{type(e).__name__}:{e}")
        return "未知"
    
def load_test_cases(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_test():
    cases = load_test_cases(DATASET_FILE)
    total = len(cases)
    results = []
    print(f"🚀 开始连接真实 AI 接口，逐条执行测试，共 {total} 条...\n")

    for case in cases:
        payload = {"questions":[case["query"]],"history": []}
        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
            if response.status_code != 200:
                print(f"[{case['id']}] ⚠️ 请求失败 (HTTP {response.status_code})")
                continue
            res_data = response.json()
            api_items = res_data.get("data",{}).get("items", [])
            if not api_items:
                continue

            item = api_items[0]
            ref_titles = item.get("ref_titles",[])
            is_kb_hit = "是" if ref_titles else "否"
            kb_content = ", ".join(ref_titles) if ref_titles else "无"
            reply_text = item.get("reply")  or item.get("rule_reply") or ""
            rule_handoff = item.get("rule_handoff", False)
            latency = item.get("latency_ms", 0) # 性能指标，消耗的时间。

            # 调用 OpenAI 为裁判 
            hallucination = judge_hallucination(
                case["query"],case["expected_intent"],reply_text, is_kb_hit
            )

            status = "✅ 有回复" if reply_text and item.get("status") == "done" else "❌ 无回复"

            result_row = {
                "ID": case["id"],
                "Query": case["query"],
                "期望意图": case["expected_intent"],  # 后台列表-关联意图说明:  模版-其它字段（json)—intent
                "期望动作": case["expected_action"],  # 知识库列表的（回答）即 详情里的机器人怎么答：模版里的 正文
                "是否命中知识库": is_kb_hit,
                "命中知识库内容": kb_content,
                "AI回复(Reply)": reply_text,
                "AI幻觉": hallucination,
                "触发转人工": rule_handoff,
                "耗时(ms)": latency,
                "接口状态": status
            }

            results.append(result_row)
            # 知识库
            display_kb = kb_content if len(kb_content) <= 15 else kb_content[:15] + "..."
            # AI 回复
            display_reply = reply_text if len(reply_text) <= 25 else reply_text[:25] + "..."

            log_str = (
                f"[{case['id']}] 命中：{is_kb_hit} | 库内容：{display_kb}"
                f"| 问：{case['query']} | AI答: {display_reply}"
            )
            # 未命中时，把"有/无/未知"都打印出来
            if is_kb_hit == "否":
                log_str += f" | 出现幻觉：{hallucination}"
            print(log_str)
        except Exception as e:
            print(f"[{case['id']}] ⚠️ 异常: {e}")

        time.sleep(0.5)

    if not results:
        return 

    # 计算并打印报表数据
    hit_count = sum(1 for r in results if r["是否命中知识库"] == "是")
    miss_count = len(results) - hit_count

    # 收集所有出现幻觉的 ID，组合成类似 "[T021]、[T045]" 的字符串
    hallucination_ids = [f"[{r['ID']}]" for r in results if r["是否命中知识库"] == "否" and r["AI幻觉"] == "有"]
    # 统计 AI幻觉的。
    miss_hallucination_count = len(hallucination_ids)
    hallucination_str = "、".join(hallucination_ids) if hallucination_ids else "无"
   
   # 统计 网络/超时/限流/JSON 解析失败 ,全部视为"未知"的。
    miss_unknown_count = sum(
        1 for r in results
        if r["是否命中知识库"] == "否" and r["AI幻觉"] == "未知"
    )

    hit_rate = (hit_count / len(results)) * 100
    print(f"\n📊 测试完成！共 {len(results)} 条。")

    # 汇总里增加"判定失败"条数
    print(
        f"🎯 知识库命中率：{hit_rate:.1f}%"
        f"(命中 {hit_count} 条，未命中 {miss_count} 条, "
        f"其中 AI回复出现幻觉 {miss_hallucination_count} 条, " # [{hallucination_str}]
        f"判定失败(未知:网络/超时/限流/JSON解析 失败的情况) {miss_unknown_count} 条)"
    )
    today_str = datetime.now().strftime("%Y%m%d_%H%M")

    # 1. 生成全量总报表（保留原有逻辑）
    output_file = f"test_result_全量_{today_str}.csv"
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
         writer = csv.DictWriter(
             f,
            fieldnames=[
                "ID", "Query", "期望意图", "期望动作", "是否命中知识库", "命中知识库内容",
                "AI回复(Reply)", "AI幻觉", "触发转人工", "耗时(ms)", "接口状态"
            ]
         )
         writer.writeheader()
         writer.writerows(results)
    print(f"💾 详细明细已保存至：{output_file}")

    # 提取“未命中且AI有幻觉”的数据，生成一份 CSV
    hallucination_cases = [r for r in results if r["是否命中知识库"] == "否" and r["AI幻觉"] == "有"]
    if hallucination_cases:
        hallu_file = f"未命中且AI幻觉明细_{today_str}.csv"
        with open(hallu_file, 'w', newline='' , encoding='utf-8-sig') as f:
            # 严格只输出运营关心的 4 个字段
            fieldnames = ["Query", "期望意图", "AI回复(Reply)", "建议操作"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for case in hallucination_cases:
                writer.writerow({
                    "Query":case["Query"],
                    "期望意图": case["期望意图"],
                    "AI回复(Reply)": case["AI回复(Reply)"],
                    "建议操作": f"AI答非所问！请去【{case['期望意图']}】下补充规则或相似问法"
                })
        print(f"💾 未命中且有AI幻觉明细数据已保存:{hallu_file}")
    else:
        print("✅ 未命中且AI幻觉：0 条，无需生成专项表。")

if __name__ == "__main__":
    run_test()



"""
测试数据集的数据。
 {
    "id": "T00001",
    "original_id": "797129403720142848_1",
    "source_dataset": "88801.xlsx",
    "query": "为什么我下注中了不结算给我",
    "difficulty": "P1",
    "expected_intent": "其它问题/空单", 
    "expected_slots": {},
    "expected_action": "请用户详细描述问题，并提供会员账号和相关截图，客服为您核实处理。",  
    "source": "88801.xlsx|会话ID=797129403720142848|访客消息第1条"
  },

"""