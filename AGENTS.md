# AGENTS.md — LangFlow-QnA 开发指南

## 项目目标
构建一个基于 LangChain + LangGraph 的知识库智能问答 Agent 系统。
**这是一个学习项目**，目标是深入理解 Agent 开发的完整流程。

## 开发原则
- **渐进式构建**：每个 Phase 产出可运行的代码，而不是大而全的架构
- **先跑通再优化**：先做最简单的链路，再迭代增强
- **测试驱动**：关键逻辑先写测试再实现
- **频繁提交**：每个 Phase 完成一个可验证的里程碑

## 技术选型
- LLM 编排: LangChain ≥0.3 + LangGraph ≥0.2
- 向量库: Phase 2 用 Chroma (本地运行，无须 Docker)
- LLM: 优先使用兼容 OpenAI API 的模型 (DeepSeek / OpenAI / 通义千问)
- 应用框架: FastAPI + Uvicorn

## 学习指引
当用户需要你帮助时：
1. 先确认当前在哪个 Phase
2. 解释该 Phase 要学习的核心概念
3. 提供可直接运行的代码
4. 完成后引导进入下一个 Phase

## 关键参考资料
- LangGraph 官方教程: https://langchain-ai.github.io/langgraph/tutorials/
- LangChain 概念文档: https://python.langchain.com/docs/concepts/
