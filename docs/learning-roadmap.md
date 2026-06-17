# 学习路线图 — 详细指引

---

## Phase 0：环境搭建 & 项目骨架

**⏱ 预计时间：30 分钟**

**学习目标：** 搭好开发环境，理解项目结构

**步骤：**

1. **安装 Python 3.11+**（如已安装可跳过）
2. **安装 Poetry**（依赖管理工具）
3. **创建虚拟环境并安装基础依赖**
4. **配置环境变量**
5. **验证：** `python -c "import langchain; print(langchain.__version__)"` 成功

**要学的概念：**
- Poetry 管理依赖 vs pip
- `.env` 配置文件模式
- 项目分层架构的意义（api / core / services / db）

**你的任务：**
```
poetry init
poetry add langchain langchain-core langgraph ...
cp .env.example .env
```

---

## Phase 1："Hello Agent" — 最简单的 LangGraph Agent

**⏱ 预计时间：1-2 小时**

**核心学习内容：**
- LangGraph 的核心概念：`StateGraph`, `Node`, `Edge`
- 状态 `TypedDict` 的设计
- 节点的输入/输出约定
- Graph 的编译与执行

**你要实现：**

```python
# 功能：一个最简单的对话 Agent
# 输入：用户问题
# 处理：调用 LLM 生成回答
# 输出：回答文本
# 节点：1 个（chat_node）
# 边：entry -> chat_node -> END
```

**关键代码文件：**
- `app/core/agent/state.py` — 定义 AgentState
- `app/core/agent/graph.py` — 定义工作流图
- `app/core/agent/nodes/chat_node.py` — LLM 调用节点
- `scripts/chat_demo.py` — 命令行交互脚本

**验证方法：**
- 在命令行运行 `python scripts/chat_demo.py`
- 输入问题，看到 LLM 回复
- 输入 "exit" 退出

**检查清单：**
- [ ] 能调用 LLM 并返回结果
- [ ] 状态在节点间正确传递
- [ ] 支持多轮对话（消息列表累积）

---

## Phase 2：基础 RAG — 让 Agent 能读取知识库

**⏱ 预计时间：3-4 小时**

**核心学习内容：**
- Document Loaders（如何读取 PDF/文本）
- Text Splitters（分块策略）
- Embeddings（文本向量化）
- Vector Stores（向量存储与检索）
- 在 LangGraph 中集成检索

**你要实现：**

```
用户问题 → 检索节点 → 生成节点 → 回答
```

**新增代码：**
- `app/ingestion/pipeline.py` — 文档导入管线
- `app/core/agent/nodes/retriever.py` — 检索节点
- `app/core/agent/nodes/generator.py` — 生成节点（带 Context）
- `scripts/ingest_docs.py` — 导入脚本
- `scripts/qa_demo.py` — 问答测试脚本

**两个运行模式：**
1. **导入模式：** `python scripts/ingest_docs.py ./docs/knowledge/`
2. **问答模式：** `python scripts/qa_demo.py`

**关键概念图解：**

```
文档 "2024年报.pdf"
    │
    ▼
[Document Loader] → [Text Splitter] → [Embedding] → [Vector Store]
                                                             │
用户 "今年营收是多少？"                                       │
    │                                                         │
    ▼                                                         │
[Embedding] ──similarity_search──▶ [相关 Chunks]              │
    │                                                         │
    ▼                                                         │
[LLM + Context] ──▶ "今年营收为 XXX 亿元"                     │
```

**检查清单：**
- [ ] 能成功导入文档到向量库
- [ ] 检索返回相关片段
- [ ] LLM 基于检索内容回答
- [ ] LLM 在文档不相关时能说"不知道"

---

## Phase 3：可控工作流 — 意图路由 + 条件分支

**⏱ 预计时间：3-4 小时**

**核心学习内容：**
- LangGraph 的 `Conditional Edge`（条件边）
- 意图识别（Intent Classification）
- 问题分解（Question Decomposition）
- 兜底逻辑（Fallback Handling）
- Graph 的可视化

**你要实现的流程：**

```
              ┌──────────┐
              │ 用户输入  │
              └────┬─────┘
                   │
              ┌────▼─────┐
              │ 意图识别   │
              └────┬─────┘
                   │
          ┌────────┼─────────┐──────────┐
          │        │         │          │
     ┌────▼───┐ ┌──▼──┐ ┌───▼────┐ ┌───▼────┐
     │ QA     │ │闲聊 │ │ 总结   │ │ 追问   │
     │ 检索+生成│ │直接回│ │全文档  │ │ 澄清   │
     └────┬───┘ └──┬──┘ └───┬────┘ └───┬────┘
          │        │         │          │
          └────────┴────┬────┴──────────┘
                        │
                   ┌────▼─────┐
                   │  输出     │
                   └──────────┘
```

**新增/修改代码：**
- `app/core/agent/nodes/intent_router.py` — 意图识别节点
- 修改 `graph.py` — 添加条件边
- `app/core/agent/nodes/fallback.py` — 兜底处理

**要学的核心概念——什么是条件边：**

```python
# 条件边 = 根据节点输出决定走哪条路
builder.add_conditional_edges(
    "intent_router",
    route_by_intent,           # 这个函数返回分支名称
    {
        "qa": "retriever",
        "chat": "chat_node",
        "fallback": "fallback",
    }
)
```

**检查清单：**
- [ ] 能区分"问答"和"闲聊"
- [ ] 闲聊不走检索直接回复
- [ ] 知识库无答案时走兜底
- [ ] 支持复杂问题分解为子问题

---

## Phase 4：质量增强 — 重排序 + 答案验证

**⏱ 预计时间：3-4 小时**

**核心学习内容：**
- 混合检索（向量 + 关键词）
- RRF（Reciprocal Rank Fusion）融合算法
- Cross-Encoder 重排序
- 幻觉检测（Hallucination Detection）
- LangGraph 的循环（Loop）—— 验证不通过则重试

**你要实现的流程：**

```
检索 → 多路结果 → RRF融合 → 重排序 → 生成 → 验证 → 通过 → 输出
                           ↑                     │
                           └──── 不通过, 重试 ────┘
```

**新增代码：**
- `app/retrieval/hybrid_search.py` — 混合检索
- `app/core/agent/nodes/reranker.py` — 重排序节点
- `app/core/agent/nodes/verifier.py` — 验证节点

**要学的核心概念——Graph 中的循环：**

```python
# LangGraph 支持循环 —— 这是普通 Chain 做不到的
builder.add_conditional_edges(
    "verifier",
    verify_quality,              # 返回 "pass" 或 "retry"
    {
        "pass": END,
        "retry": "retriever",    # 重新检索再生成
    }
)
```

**检查清单：**
- [ ] 混合检索比纯向量检索效果更好
- [ ] 重排序后 Top-K 结果更准确
- [ ] 能检测到回答中的幻觉
- [ ] 验证不通过时自动重试

---

## Phase 5：生产化 — FastAPI 服务 + 对话记忆

**⏱ 预计时间：2-3 小时**

**核心学习内容：**
- FastAPI 与 LangGraph 集成
- SSE / WebSocket 流式输出
- 对话历史的持久化（短期 + 长期记忆）
- LangGraph Checkpointer（断点续传）
- Docker 部署

**新增代码：**
- `app/api/routes/chat.py` — 对话 API
- `app/services/session.py` — 会话管理
- `app/memory/buffer_memory.py` — 缓冲记忆
- `app/memory/persistent_memory.py` — 持久记忆（PostgreSQL）
- `docker-compose.yml`

**检查清单：**
- [ ] API 接受请求并返回流式响应
- [ ] 多轮对话能记住上下文
- [ ] 对话历史从数据库恢复
- [ ] Docker 一键启动

---

## Phase 6：评估与优化

**⏱ 预计时间：2-3 小时**

**核心学习内容：**
- RAG 评估指标体系
- LangSmith Trace 追踪
- 自动化测试（单元 + 集成）
- 性能优化（缓存、并发）

**新增代码：**
- `tests/unit/test_nodes.py`
- `tests/integration/test_graph.py`
- `scripts/eval_pipeline.py`

**评估指标：**
- 检索召回率 (Recall@K)
- 答案准确性 (Answer Correctness)
- 引用精度 (Citation Precision)
- 端到端延迟 (Latency P50/P95)

**检查清单：**
- [ ] 有自动化测试覆盖核心节点
- [ ] 有端到端工作流测试
- [ ] LangSmith 能追踪每次调用
- [ ] 知道系统当前的性能基线

---

## 📌 学习建议

1. **只看一个 Phase 的文档，不要提前看后面的** — 保持好奇心
2. **每完成一个 Phase，在 Git 里打个 tag** — `git tag phase-1`
3. **卡住了先看错误信息，再看官方文档，最后问我**
4. **多跑println / 加日志** — 理解数据在 Graph 中的流转
5. **不要跳过 Phase 直接做后面的** — 每个 Phase 依赖前面的概念
