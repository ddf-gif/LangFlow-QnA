<p align="center">
  <img src="https://img.shields.io/badge/LangChain-≥0.3-1C3C3C?logo=langchain" alt="LangChain" />
  <img src="https://img.shields.io/badge/LangGraph-≥0.2-1C3C3C?logo=langgraph" alt="LangGraph" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License" />
</p>

<div align="center">
  <h1>LangFlow QnA</h1>
  <p><strong>B 端管理 + C 端使用的知识库智能问答平台</strong></p>
  <p>意图路由 → 语义检索 → 重排序 → 验证循环，全链路可控 Agent 工作流</p>
</div>

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户访问                                  │
└──────────┬────────────────────────────────┬─────────────────────┘
           │                                │
           ▼                                ▼
┌─────────────────────┐    ┌─────────────────────────────────────┐
│  C 端用户问答界面    │    │  B 端管理后台                        │
│  /                   │    │  /admin/                            │
│  简洁对话页           │    │  文档管理 / Agent 配置 / 角色管理   │
│  对话历史侧栏         │    │  数据看板 / 分类管理               │
│  引用来源展示         │    │                                     │
└──────────┬───────────┘    └──────────┬──────────────────────────┘
           │                           │
           └──────────┬───────────────┘
                      ▼
           ┌─────────────────────┐
           │   FastAPI 后端       │
           │   /api/*            │
           └──────────┬──────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
   ┌─────────┐ ┌───────────┐ ┌──────────┐
   │ Chroma  │ │  JSON 文件 │ │  LLM    │
   │ 向量库  │ │  持久化    │ │  API    │
   └─────────┘ └───────────┘ └──────────┘
```

## 特性

| 特性 | 说明 |
|------|------|
| **🔐 用户认证** | JWT 令牌，支持注册/登录，管理员与普通用户角色分离 |
| **🧠 C 端问答** | 简洁对话界面，左侧历史记录栏，对话持久化存储 |
| **⚙️ B 端管理** | 文档上传/管理、Agent 配置、角色管理、数据看板 |
| **📚 知识库分类** | 自定义分类目录，文档按分类组织 |
| **💬 多轮对话** | 基于 LangGraph Checkpointer 的会话记忆 |
| **🔍 语义检索** | 本地 BGE 嵌入模型 + Chroma 向量库 |
| **🎯 意图识别** | LLM 自动分类问题类型（QA / 闲聊 / 无法处理） |
| **✅ 答案验证** | 幻觉检测 + 引用验证，不通过则重新检索 |
| **🎨 极简 UI** | 黑白极简风格，响应式设计，暗色模式（B 端） |
| **📄 文件上传** | 支持 .txt / .md / .py / .js / .ts / .json / .csv |

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

# 编辑 .env 填入你的配置
#   LLM_API_KEY=sk-your-key
#   LLM_BASE_URL=https://api.deepseek.com/v1
#   LLM_MODEL=deepseek-chat
#
#   # 管理员账号（默认 admin / admin123）
#   ADMIN_USERNAME=admin
#   ADMIN_PASSWORD=admin123
```

### 启动

```bash
# 启动 Web 服务（推荐使用离线模式避免 SSL 问题）
set HF_HUB_OFFLINE=1 && uvicorn app.main:app --reload --port 8765
```

服务启动后，打开浏览器访问 `http://localhost:8765/login` 即可进入登录页面。

默认端口为 `8765`，可在启动命令中通过 `--port` 参数修改。

### 访问地址

| 页面 | 路径 | 说明 |
|------|------|------|
| 🔐 登录/注册 | `/login` | 注册或登录 |
| 🧠 C 端问答 | `/` | 用户问答界面（需登录） |
| ⚙️ B 端管理 | `/admin/` | 管理后台（需管理员登录） |
| 📖 API 文档 | `/docs` | Swagger 文档 |

> 以上路径均相对于服务部署地址，例如部署在 `http://localhost:8765` 则对应 `http://localhost:8765/login`。

### 默认管理员账号

| 用户名 | 密码 |
|--------|------|
| `admin` | `admin123` |

> 普通用户请在登录页面点击「注册」自行创建账号。

### 导入知识文档

```bash
# 方式一：通过管理后台网页上传
# 访问部署地址的 /admin/ → 文档管理 → 上传

# 方式二：命令行导入
python scripts/ingest_docs.py
```

> 首次运行会自动下载 BGE 中文嵌入模型（约 30MB，仅需一次）。

---

## 项目结构

```
LangFlow-QnA/
├── app/
│   ├── main.py                       # FastAPI 入口
│   ├── config.py                     # pydantic-settings 配置
│   ├── core/agent/                   # ★ LangGraph 工作流核心
│   │   ├── state.py                  # Agent 状态定义
│   │   ├── graph.py                  # 工作流图
│   │   └── nodes/                    # 各节点实现
│   │       ├── intent_router.py      #   意图识别
│   │       ├── retriever.py          #   向量检索
│   │       ├── reranker.py           #   LLM 重排序
│   │       ├── generator.py          #   答案生成
│   │       ├── verifier.py           #   验证 & 幻觉检测
│   │       ├── chat_node.py          #   闲聊
│   │       └── fallback.py           #   兜底
│   ├── retrieval/
│   │   └── vector_store.py           # Chroma 封装
│   ├── ingestion/
│   │   └── pipeline.py               # 文档导入管线
│   ├── api/routes/
│   │   ├── auth.py                   # 用户认证 API
│   │   ├── chat.py                   # 对话 API
│   │   ├── conversations.py          # 对话记录 API
│   │   ├── documents.py              # 文档管理 API
│   │   ├── stats.py                  # 数据看板 API
│   │   ├── categories.py            # 分类管理 API
│   │   └── roles.py                  # 角色管理 API
│   ├── services/
│   │   ├── auth.py                   # JWT + 密码哈希
│   │   ├── conversations.py          # 对话记录持久化
│   │   ├── doc_registry.py           # 文档注册表
│   │   ├── roles.py                  # 角色管理
│   │   └── session.py                # 会话管理
│   └── static/
│       ├── index.html                # C 端问答页面
│       ├── login.html                # 登录/注册页面
│       └── admin/
│           └── index.html            # B 端管理后台
├── scripts/
│   └── ingest_docs.py                # 文档导入脚本
├── tests/
├── data/
│   ├── knowledge/                    # 默认知识文档目录
│   ├── uploads/                      # 上传文档目录
│   ├── vector_store/                 # Chroma 持久化
│   ├── doc_registry.json             # 文档元数据
│   ├── categories.json               # 分类列表
│   ├── roles.json                    # 角色数据
│   ├── users.json                    # 用户数据
│   └── conversations.json            # 对话记录
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## API 文档

启动服务后访问 `/docs` 查看完整的 Swagger 文档（例如部署在 `http://localhost:8765` 则访问 `http://localhost:8765/docs`）。

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 当前用户信息 |
| `/api/chat` | POST | 对话问答 |
| `/api/chat/stream` | POST | 流式对话 (SSE) |
| `/api/conversations` | GET | 对话列表 |
| `/api/conversations` | POST | 创建对话 |
| `/api/conversations/{id}` | GET | 对话详情（含消息） |
| `/api/conversations/{id}` | DELETE | 删除对话 |
| `/api/conversations/{id}/messages` | POST | 追加消息 |
| `/api/documents` | GET | 文档列表 |
| `/api/documents/upload` | POST | 上传文档 |
| `/api/documents/{id}` | GET | 文档详情 |
| `/api/documents/{id}` | DELETE | 删除文档 |
| `/api/documents/reindex` | POST | 重索引 |
| `/api/documents/batch-category` | POST | 批量分类 |
| `/api/categories` | GET | 分类列表 |
| `/api/categories` | POST | 创建分类 |
| `/api/roles` | GET | 角色列表 |
| `/api/roles` | POST | 创建角色 |
| `/api/roles/{id}` | DELETE | 删除角色 |
| `/api/stats` | GET | 数据看板统计 |
| `/health` | GET | 健康检查 |

### 示例

```bash
# 注册
curl -X POST https://your-domain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypass123"}'

# 登录
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 问答（需传入 token）
TOKEN="your-jwt-token"
curl -X POST https://your-domain.com/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "2024年营收多少", "session_id": "test-1"}'

# 上传文档
curl -X POST https://your-domain.com/api/documents/upload \
  -F "file=@report.txt"
```

> 将 `your-domain.com` 替换为实际部署地址，本地开发可用 `localhost:8765`。

---

## 技术栈

| 类别 | 技术 |
|------|------|
| LLM 编排 | LangChain ≥0.3, LangGraph ≥0.2 |
| 向量库 | Chroma (本地, 无须 Docker) |
| 嵌入模型 | BAAI/bge-small-zh-v1.5 (本地, 30MB) |
| LLM | 兼容 OpenAI API (DeepSeek / OpenAI / 通义千问) |
| 服务框架 | FastAPI + Uvicorn |
| 认证 | JWT (python-jose) + bcrypt |
| C 端前端 | 纯 HTML/CSS/JS (极简黑白风格) |
| B 端前端 | 纯 HTML/CSS/JS (管理后台) |
| 存储 | JSON 文件 / Chroma 向量库 |

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

## License

MIT
