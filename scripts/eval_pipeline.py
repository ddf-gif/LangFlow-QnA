"""
评估脚本 — 测试 RAG 问答质量。

用法:
    python scripts/eval_pipeline.py

评估指标:
    - 关键词命中率（Answer Hit Rate）: 预期关键词出现在回答中的比例
    - 检索召回率（Retrieval Recall）: 关联文档是否被检索到
    - 综合得分: 各指标加权平均
    - 按分类分组统计

输出:
    - 控制台摘要
    - HTML 报告文件（eval_report.html）
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.agent.graph import agent_graph

CASES_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_cases.json"
REPORT_PATH = Path(__file__).resolve().parent.parent / "eval_report.html"


def load_cases():
    """加载测试用例。"""
    if not CASES_PATH.exists():
        print(f"[错误] 测试用例文件不存在: {CASES_PATH}")
        sys.exit(1)
    with open(CASES_PATH, encoding="utf-8") as f:
        return json.load(f)


def evaluate():
    """运行评估，生成 HTML 报告。"""
    cases = load_cases()
    total = len(cases)
    results = []

    print("=" * 60)
    print(f"LangFlow-QnA 评估报告 ({total} 个用例)")
    print("=" * 60)

    for i, case in enumerate(cases, 1):
        thread_id = f"eval-{i}"
        q = case["question"]
        expected_keywords = case.get("expected_keywords", [])
        relevant_docs = case.get("relevant_docs", [])

        try:
            result = agent_graph.invoke(
                {"messages": [("human", q)]},
                config={"configurable": {"thread_id": thread_id}},
            )
            answer = result["messages"][-1].content

            # 检索到的文档
            retrieved = set()
            retrieved_docs = result.get("retrieved_docs", [])
            for doc in retrieved_docs:
                src = doc.metadata.get("source", "")
                # 只取文件名部分
                retrieved.add(Path(src).name if src else src)

            # 指标 1: 关键词命中
            hits = [kw for kw in expected_keywords if kw.lower() in answer.lower()]
            hit_rate = len(hits) / len(expected_keywords) if expected_keywords else 0

            # 指标 2: 检索召回（关联文档是否被检索到）
            if relevant_docs:
                relevant_set = set(relevant_docs)
                recalled = relevant_set & retrieved
                recall = len(recalled) / len(relevant_set) if relevant_set else 0
            else:
                recalled = set()
                recall = None

            passed = hit_rate >= 0.5  # 至少命中一半关键词才算通过

            status = "✅" if passed else "❌"
            print(f"\n{status} [{case.get('category','通用')}] {q}")
            print(f"   关键词命中: {hits}/{expected_keywords}")
            if recall is not None:
                print(f"   检索召回: {recalled}/{relevant_set}")
            print(f"   回答片段: {answer[:60]}...")

            results.append({
                "id": case.get("id", f"case-{i}"),
                "category": case.get("category", "通用"),
                "question": q,
                "answer": answer,
                "expected_keywords": expected_keywords,
                "hit_keywords": hits,
                "hit_rate": round(hit_rate * 100, 1),
                "relevant_docs": relevant_docs,
                "retrieved_docs": list(retrieved),
                "recall": round(recall * 100, 1) if recall is not None else None,
                "passed": passed,
            })
        except Exception as e:
            print(f"\n❌ [{case.get('category','通用')}] {q}")
            print(f"   错误: {e}")
            results.append({
                "id": case.get("id", f"case-{i}"),
                "category": case.get("category", "通用"),
                "question": q,
                "answer": f"[错误] {e}",
                "expected_keywords": expected_keywords,
                "hit_keywords": [],
                "hit_rate": 0,
                "relevant_docs": relevant_docs,
                "retrieved_docs": [],
                "recall": 0,
                "passed": False,
            })

    # ── 汇总统计 ──
    total_passed = sum(1 for r in results if r["passed"])
    avg_hit = sum(r["hit_rate"] for r in results) / total if total else 0
    avg_recall_list = [r["recall"] for r in results if r["recall"] is not None]
    avg_recall = sum(avg_recall_list) / len(avg_recall_list) if avg_recall_list else None

    # 按分类统计
    cats: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        if cat not in cats:
            cats[cat] = {"total": 0, "passed": 0, "hit_sum": 0}
        cats[cat]["total"] += 1
        cats[cat]["passed"] += 1 if r["passed"] else 0
        cats[cat]["hit_sum"] += r["hit_rate"]

    # ── 输出汇总 ──
    print(f"\n{'=' * 60}")
    print(f"📊 汇总")
    print(f"{'=' * 60}")
    print(f"综合通过率: {total_passed}/{total} ({total_passed/total*100:.0f}%)")
    print(f"平均关键词命中率: {avg_hit:.1f}%")
    if avg_recall is not None:
        print(f"平均检索召回率: {avg_recall:.1f}%")
    print()
    for cat, st in sorted(cats.items()):
        print(f"  {cat}: {st['passed']}/{st['total']} 通过, 命中率 {st['hit_sum']/st['total']:.1f}%")

    # ── 生成 HTML 报告 ──
    _gen_html_report(results, avg_hit, avg_recall, total_passed, total, cats)

    print(f"\n📄 HTML 报告已生成: {REPORT_PATH}")


def _gen_html_report(results, avg_hit, avg_recall, total_passed, total, cats):
    """生成可视化 HTML 评估报告。"""
    rows = ""
    for r in results:
        status = "✅" if r["passed"] else "❌"
        kw = ", ".join(r["hit_keywords"]) if r["hit_keywords"] else "—"
        docs = ", ".join(r["retrieved_docs"]) if r["retrieved_docs"] else "—"
        rows += f"""
        <tr>
            <td>{status}</td>
            <td>{r['category']}</td>
            <td>{r['question'][:40]}</td>
            <td>{r['hit_rate']}%</td>
            <td>{r['recall'] or '—'}%</td>
            <td>{kw}</td>
            <td>{docs}</td>
        </tr>"""

    cat_rows = ""
    for cat, st in sorted(cats.items()):
        cat_rows += f"<tr><td>{cat}</td><td>{st['passed']}/{st['total']}</td><td>{st['hit_sum']/st['total']:.1f}%</td></tr>"

    avg_r = round(avg_recall, 1) if avg_recall else "—"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>LangFlow 评估报告</title>
<style>
body{{font-family:'Noto Sans SC',sans-serif;background:#f5f5f5;color:#1a1a1a;padding:24px;max-width:1000px;margin:auto}}
h1{{font-size:22px;font-weight:700;margin-bottom:4px}}
.date{{color:#666;font-size:13px;margin-bottom:20px}}
.summary{{display:flex;gap:16px;margin-bottom:24px}}
.sm-card{{background:#fff;border-radius:8px;padding:16px 20px;flex:1;border:1px solid #e0e0e0}}
.sm-card .val{{font-size:28px;font-weight:700}}
.sm-card .lbl{{font-size:12px;color:#666;margin-top:2px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #e0e0e0}}
th{{text-align:left;padding:10px 12px;font-size:11px;font-weight:600;color:#666;text-transform:uppercase;border-bottom:1px solid #e0e0e0;background:#fafafa}}
td{{padding:10px 12px;font-size:13px;border-bottom:1px solid #f0f0f0}}
tr:last-child td{{border:none}}
.pass{{color:#4CAF84}}
.fail{{color:#E53935}}
</style>
</head>
<body>
<h1>🧠 LangFlow 评估报告</h1>
<div class="date">{datetime.now().strftime('%Y-%m-%d %H:%M')} · {total} 个用例</div>
<div class="summary">
  <div class="sm-card"><div class="val">{total_passed}/{total}</div><div class="lbl">综合通过率</div></div>
  <div class="sm-card"><div class="val">{avg_hit:.1f}%</div><div class="lbl">平均关键词命中率</div></div>
  <div class="sm-card"><div class="val">{avg_r}%</div><div class="lbl">平均检索召回率</div></div>
</div>

<h2 style="font-size:16px;font-weight:600;margin-bottom:12px">📂 按分类</h2>
<table><thead><tr><th>分类</th><th>通过</th><th>命中率</th></tr></thead>
<tbody>{cat_rows}</tbody></table>

<h2 style="font-size:16px;font-weight:600;margin:24px 0 12px">📋 详细结果</h2>
<table><thead><tr><th>状态</th><th>分类</th><th>问题</th><th>命中率</th><th>召回率</th><th>命中关键词</th><th>检索来源</th></tr></thead>
<tbody>{rows}</tbody></table>
</body>
</html>"""
    REPORT_PATH.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    evaluate()
