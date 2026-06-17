# LangFlow-QnA

基于 LangChain + LangGraph 的知识库智能问答 Agent 系统。

## 功能

- 基于知识库文档的智能问答（RAG）
- 意图识别路由（问答 / 闲聊 / 总结）
- 文档重排序 + 答案验证防幻觉
- 多轮对话记忆
- 流式输出 API
- 命令行交互模式

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt  # 或: pip install .

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 3. 导入知识文档
set HF_ENDPOINT=https://hf-mirror.com
python scripts/ingest_docs.py

# 4. 命令行问答
python -X utf8 -m app.core.agent.graph

# 5. 启动 API 服务
uvicorn app.main:app --reload
```

## 项目结构

```
app/
├── main.py              # FastAPI 入口
├── config.py            # 配置管理
├── core/agent/          # LangGraph 工作流
│   ├── state.py         # Agent 状态定义
│   ├── graph.py         # 工作流图
│   └── nodes/           # 各处理节点
├── retrieval/           # 检索模块
├── ingestion/           # 文档导入管线
├── api/routes/          # HTTP 接口
└── services/            # 服务层
scripts/                 # 工具脚本
tests/                   # 测试
```

## 工作流

```
用户输入 → 意图识别
  ├─ QA 问答 → 检索 → 重排序 → 生成 → 验证 → 输出
  ├─ 闲聊 → 直接对话
  └─ 无法处理 → 兜底回复
```
