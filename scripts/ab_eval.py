"""
A/B 评估 — 对比旧检索器 vs 新检索器（多路召回 + 句子窗口）的命中率差异。

原理：通过切换 app.core.agent.nodes.retriever.BASELINE_MODE 标志
      在基线（单路向量检索）和改进（多路召回）模式间切换。

用法:
    python scripts/ab_eval.py

输出:
    - 控制台对比报告
    - ab_eval_report.html（可视化对比）
"""
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.agent.graph import agent_graph
from app.core.agent.nodes import retriever as retriever_module

CASES_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_cases.json"
REPORT_PATH = Path(__file__).resolve().parent.parent / "ab_eval_report.html"


def _run_eval(label: str, baseline_mode: bool) -> list:
    """设置 BASELINE_MODE，运行一轮评估。"""
    # 直接设置标志（不用 reload，因为 retriever_node 在调用时实时读取这个标志）
    retriever_module.BASELINE_MODE = baseline_mode

    print(f"\n{'='*60}")
    print(f"  模式: {label}")
    print(f"{'='*60}")

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    results = []

    for i, case in enumerate(cases, 1):
        q = case["question"]
        e_kw = case.get("expected_keywords", [])
        r_docs = case.get("relevant_docs", [])
        try:
            result = agent_graph.invoke(
                {"messages": [("human", q)]},
                config={"configurable": {"thread_id": f"ab-{'base' if baseline_mode else 'imp'}-{i}"}},
            )
            answer = result["messages"][-1].content
            retrieved = set()
            for doc in result.get("retrieved_docs", []):
                src = doc.metadata.get("source", "")
                retrieved.add(Path(src).name if src else src)

            hits = [kw for kw in e_kw if kw.lower() in answer.lower()]
            hit_rate = len(hits) / len(e_kw) if e_kw else 0
            recall = len(set(r_docs) & retrieved) / len(r_docs) if r_docs else None

            results.append({
                "id": case.get("id", f"c{i}"),
                "category": case.get("category", "通用"),
                "question": q[:50],
                "hit_rate": round(hit_rate * 100, 1),
                "recall": round(recall * 100, 1) if recall is not None else None,
                "hit_keywords": hits,
                "retrieved_docs": list(retrieved),
            })
            status = "✅" if hit_rate >= 50 else "❌"
            print(f"  {status} [{case.get('category','')}] {q[:40]} → 命中率 {results[-1]['hit_rate']}%")
        except Exception as e:
            print(f"  ❌ [{case.get('category','')}] {q[:40]} → {e}")

    return results


def main():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    total = len(cases)

    print("=" * 60)
    print("  LangFlow A/B 评估 — 检索器对比")
    print(f"  用例: {total}  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 先跑基线，再跑改进
    baseline = _run_eval("baseline（单路向量检索）", baseline_mode=True)
    improved = _run_eval("improved（多路召回 + 句子窗口）", baseline_mode=False)

    if not baseline or not improved:
        return

    # 对比统计
    b_hit = sum(r["hit_rate"] for r in baseline) / total
    i_hit = sum(r["hit_rate"] for r in improved) / total
    b_rec = sum(r["recall"] or 0 for r in baseline) / total
    i_rec = sum(r["recall"] or 0 for r in improved) / total
    b_pass = sum(1 for r in baseline if r["hit_rate"] >= 50)
    i_pass = sum(1 for r in improved if r["hit_rate"] >= 50)

    print(f"\n{'='*60}")
    print(f"  📊 对比结果")
    print(f"{'='*60}")
    print(f"  指标           基线(baseline)  改进(improved)  变化")
    print(f"  {'─'*55}")
    print(f"  关键词命中率   {b_hit:>7.1f}%       {i_hit:>7.1f}%       {'+' if i_hit>=b_hit else ''}{i_hit-b_hit:>+.1f}%")
    print(f"  检索召回率     {b_rec:>7.1f}%       {i_rec:>7.1f}%       {'+' if i_rec>=b_rec else ''}{i_rec-b_rec:>+.1f}%")
    print(f"  通过率         {b_pass}/{total} ({b_pass/total*100:.0f}%)                {i_pass}/{total} ({i_pass/total*100:.0f}%)")

    # 逐用例表格
    rows = ""
    for b, im in zip(baseline, improved):
        diff = im["hit_rate"] - b["hit_rate"]
        arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
        cls = "up" if diff > 0 else ("down" if diff < 0 else "")
        rows += f"""<tr><td>{b['category']}</td><td>{b['question'][:30]}</td>
<td class="{cls}">{b['hit_rate']}% → {im['hit_rate']}% {arrow} {diff:+.1f}%</td>
<td>{b.get('recall','—') or '—'}% → {im.get('recall','—') or '—'}%</td>
<td>{', '.join(b['hit_keywords'][:2]) or '—'}</td>
<td>{', '.join(im['hit_keywords'][:2]) or '—'}</td></tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>A/B 评估报告</title>
<style>
body{{font-family:'Noto Sans SC',sans-serif;background:#f5f5f5;color:#1a1a1a;padding:24px;max-width:1000px;margin:auto}}
h1{{font-size:22px;font-weight:700}}.date{{color:#666;font-size:13px;margin-bottom:20px}}
.summary{{display:flex;gap:16px;margin-bottom:24px}}
.sc{{background:#fff;border-radius:8px;padding:16px 20px;flex:1;border:1px solid #e0e0e0}}
.sc .v{{font-size:26px;font-weight:700}}.sc .l{{font-size:12px;color:#666;margin-top:2px}}.sc .s{{font-size:13px;margin-top:4px}}
.up{{color:#4CAF84}}.down{{color:#E53935}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #e0e0e0}}
th{{text-align:left;padding:10px 12px;font-size:11px;font-weight:600;color:#666;border-bottom:1px solid #e0e0e0;background:#fafafa}}
td{{padding:10px 12px;font-size:13px;border-bottom:1px solid #f0f0f0}}
</style>
</head>
<body>
<h1>🧠 A/B 评估 — 检索器对比</h1>
<div class="date">{datetime.now().strftime('%Y-%m-%d %H:%M')} · 基线: 单路向量检索 vs 改进: 多路召回+句子窗口</div>
<div class="summary">
<div class="sc"><div class="v">{b_hit:.1f}%</div><div class="l">基线命中率</div></div>
<div class="sc"><div class="v">{i_hit:.1f}%</div><div class="l">改进命中率</div><div class="s up">+{i_hit-b_hit:.1f}%</div></div>
<div class="sc"><div class="v">{b_rec:.1f}%</div><div class="l">基线召回率</div></div>
<div class="sc"><div class="v">{i_rec:.1f}%</div><div class="l">改进召回率</div><div class="s up">+{i_rec-b_rec:.1f}%</div></div>
</div>
<h2 style="font-size:16px;font-weight:600;margin-bottom:12px">📋 逐用例对比</h2>
<table><thead><tr><th>分类</th><th>问题</th><th>命中率变化</th><th>召回率变化</th><th>基线命中词</th><th>改进命中词</th></tr></thead>
<tbody>{rows}</tbody></table>
</body></html>"""
    REPORT_PATH.write_text(html, encoding="utf-8")
    print(f"\n📄 HTML 报告: {REPORT_PATH}")


if __name__ == "__main__":
    main()
