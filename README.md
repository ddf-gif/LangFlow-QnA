<p align="center">
  <img src="https://img.shields.io/badge/LangChain-≥0.3-1C3C3C?logo=langchain" alt="LangChain" />
  <img src="https://img.shields.io/badge/LangGraph-≥0.2-1C3C3C?logo=langgraph" alt="LangGraph" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License" />
</p>

<div align="center">
  <h1>LangFlow QnA</h1>
  <p><strong>基于 LangChain + LangGraph 的知识库智能问答 Agent 系统</strong></p>
  <p>意图路由 → 语义检索 → 重排序 → 验证循环，全链路可控 Agent 工作流</p>
</div>

---

## 系统架构

```
用户输入
    │
    ▼
┌────────────────────────────────────────────────────────┐
│                   意图识别 (Intent Router)               │
│                    LLM 分类问题类型                      │
└────────┬──────────┬──────────────┬──────────────────────┘
         │          │              │
    ┌────┴────┐ ┌───┴───┐  ┌─────┴──────┐
    │  QA     │ │ 闲聊  │  │ 无法处理   │
    │ 知识问答│ │直接对话│  │ 兜底回复   │
    └────┬────┘ └───┬───┘  └─────┬──────┘
         │          └──────┬──────┘
         ▼                 ▼
┌──────────────────┐  ┌──────────┐
│  向量检索         │  │LLM 直接  │
│  Chroma + BGE     │  │回复      │
└────────┬─────────┘  └──────────┘
         │
         ▼
┌──────────────────┐
│  LLM 重排序      │
│  Top-K 精排       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  答案生成        │
│  RAG + 上下文     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  验证节点        │ ← 不通过 → 重新检索 (最多 2 次)
│  幻觉检测/引用检查│
└────────┬─────────┘
         │ 通过
         ▼
      最终输出
```

---

## 特性

- **可控工作流** — LangGraph StateGraph 驱动，7 个节点 + 条件路由 + 验证循环
- **语义检索** — 本地 BGE 嵌入模型 + Chroma 向量库，支持中文
- **意图识别** — LLM 自动分类问题类型（QA / 闲聊 / 无法处理）
- **LLM 重排序** — 对检索结果二次精排，提升相关度
- **答案验证** — 自动检查是否产生幻觉，不通过则重新检索
- **多轮对话** — Checkpointer 机制，同一会话自动记忆历史
- **文件上传** — 拖拽上传文档，实时导入知识库
- **流式 API** — FastAPI + SSE 流式输出（可选）
- **暗色 UI** — 霓虹暗色主题前端，响应式设计

---

## 快速开始

### 前置要求

- Python 3.10+
- 一个兼容 OpenAI API 的 LLM（DeepSeek / OpenAI / 通义千问 等）

### 安装

```bash
# 克隆仓库
git clone https://github.com/ddf-gif/LangFlow-QnA.git
cd LangFlow-QnA

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填入你的 API Key
# 以 DeepSeek 为例：
#   LLM_API_KEY=sk-your-key
#   LLM_BASE_URL=https://api.deepseek.com/v1
#   LLM_MODEL=deepseek-chat
```

### 导入知识文档

```bash
# Windows (PowerShell)
$env:HF_ENDPOINT = "https://hf-mirror.com"
python scripts/ingest_docs.py

# 或导入自定义文档:
# python scripts/ingest_docs.py --dir ./my_docs
```

> 首次运行会自动下载 BGE 中文嵌入模型（约 30MB）。

### 启动

#### ① 命令行模式（适合快速测试）

```bash
python -X utf8 -m app.core.agent.graph
```

#### ② Web 服务模式（推荐）

```bash
uvicorn app.main:app --reload
```

打开 **http://127.0.0.1:8000** 访问前端界面。

---

## 项目结构

```
LangFlow-QnA/
├── app/
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # pydantic-settings 配置
│   ├── core/agent/                # ★ LangGraph 工作流核心
│   │   ├── state.py               # Agent 状态定义 (TypedDict)
│   │   ├── graph.py               # 工作流图 (7 个节点 + 条件边)
│   │   └── nodes/                 # 各节点实现
│   │       ├── intent_router.py   #   意图识别
│   │       ├── retriever.py       #   向量检索
│   │       ├── reranker.py        #   LLM 重排序
│   │       ├── generator.py       #   答案生成
│   │       ├── verifier.py        #   验证 & 幻觉检测
│   │       ├── chat_node.py       #   闲聊
│   │       └── fallback.py        #   兜底
│   ├── retrieval/
│   │   └── vector_store.py        # Chroma 封装
│   ├── ingestion/
│   │   └── pipeline.py            # 文档导入管线
│   ├── api/routes/
│   │   ├── chat.py                # 对话 API (含 SSE 流式)
│   │   └── documents.py           # 文件上传 API
│   ├── static/
│   │   └── index.html             # 前端界面
│   └── services/
│       └── session.py             # 会话管理
├── scripts/
│   ├── ingest_docs.py             # 文档导入脚本
│   └── eval_pipeline.py           # 问答质量评估
├── tests/
│   ├── unit/                      # 单元测试
│   └── integration/               # 集成测试
├── data/
│   └── knowledge/                 # 默认知识文档目录
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## API 文档

启动服务后访问 **http://127.0.0.1:8000/docs** 查看完整的 Swagger 文档。

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 对话问答 |
| `/api/chat/stream` | POST | 流式对话 (SSE) |
| `/api/documents/upload` | POST | 上传文档到知识库 |
| `/health` | GET | 健康检查 |
| `/` | GET | 前端界面 |

### 示例

```bash
# 问答
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "2024年营收多少", "session_id": "test-1"}'

# 上传文档
curl -X POST http://127.0.0.1:8000/api/documents/upload \
  -F "file=@report.txt"
```

---

## 学习路线

本项目按 Phase 渐进式构建，适合学习 Agent 开发：

| Phase | 核心概念 | 学习目标 |
|-------|---------|---------|
| **1** | StateGraph, Node, Edge | LangGraph 基础工作流 |
| **2** | RAG, Embedding, Vector Store | 文档检索增强生成 |
| **3** | Conditional Edge, Intent Router | 可控 Agent 路由 |
| **4** | Reranker, Verifier, Loops | 质量保障与验证循环 |
| **5** | FastAPI, Streaming, SSE | 生产化部署 |
| **6** | Testing, Evaluation | 评估与测试 |

---

## 技术栈

| 类别 | 技术 |
|------|------|
| LLM 编排 | LangChain ≥0.3, LangGraph ≥0.2 |
| 向量库 | Chroma (本地, 无须 Docker) |
| 嵌入模型 | BAAI/bge-small-zh-v1.5 (本地, 30MB) |
| LLM | 兼容 OpenAI API (DeepSeek / OpenAI / 通义千问) |
| 服务框架 | FastAPI + Uvicorn |
| 前端 | 纯 HTML/CSS/JS (暗色霓虹主题) |

---

## License

MIT
