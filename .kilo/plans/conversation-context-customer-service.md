# 客服改造对话上下文摘要

保存时间：2026-11-09
关联计划：`.kilo/plans/1794109724330-customer-service-transformation.md`

## 项目背景
- 当前项目：`/Users/frank/Desktop/workspace/my-test-framework`（单体 FastAPI + pytest 测试框架）
- 对比项目：`/Users/frank/Desktop/work/AI_Group`（四仓库：AI_Customer_Backend/Frontend + AI_Customer_Sys_Backend/Frontend + AI_Test_Framework）
- 现有 AI 能力：`src/framework/ai/aicompanion_v1`（Streamlit）、`aicompanion_v2`（FastAPI + RAG）、`knowledge_simple`（文档检索，Qdrant）

## 用户目标
1. 将 AI 智能伴侣改造成智能客服，架构对齐 AI_Group。
2. 在当前项目增加模块和功能，便于学习提高技术能力。

## 已确认关键决策

| 决策 | 选择 |
|------|------|
| 仓库形态 | 单体仓库，内部复制 AI_Group 后端包结构（`backend/app/cs/`, `engine/`, `admin/`, `task/`, `plugin/`, `common/`, `database/`） |
| 数据库 | PostgreSQL + SQLAlchemy 异步（asyncpg）+ alembic 迁移，所有业务表加 `tenant_id` |
| 认证 | JWT（python-jose，无状态） |
| 向量存储 | Qdrant（保留现有基础设施） |
| 角色模型 | member（客户）/ agent（坐席）/ admin（后台管理员） |
| 现有路由 | 并行保留（旧伴侣 `/api/chat/*`, `/api/sessions/*` 不删，新客服路由另起） |
| 数据迁移 | 新表并存，旧表不迁移（`ai_sessions`/`ai_messages` 保留原样） |
| 前端 | 先改造现有静态 HTML 作为客服聊天页，后续再接 Vue |
| 学生管理模块 | 保留，作为可接入的业务子系统/集成示例 |

## 待办与约束
- 实施需切换到可执行代码变更的模式（当前为 plan 模式）。
- `.kilo/plans/1793804462674-customer-service-plan.md` 为早期简略版，建议删除（用户可手动 `rm`）。

## 对话要点
- 对比了两个项目架构、技术栈、AI 能力、实时通信、异步任务、测试体系、多租户等维度。
- 详细实施计划（三阶段 MVP → 座席后台 → 监控运营）已写入关联计划文件。
- 旧伴侣路由与旧数据表保留，便于新旧对比学习与回归验证。
