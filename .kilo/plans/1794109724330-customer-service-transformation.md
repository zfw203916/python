# 客服系统改造计划（基于 AI_Group 架构，单体仓库实现）

## 目标
将 `src/framework/ai/aicompanion_v2` 的 AI 智能伴侣改造成智能客服系统，架构对齐 `AI_Group/AI_Customer_Backend`：
- 知识库优先 + LLM 兜底（带领域边界）
- 多租户 + member/agent/admin 三角色
- Socket.IO 实时推送 + Celery 异步任务
- 可运行的单体 FastAPI 项目，便于学习与验证

## 关键决策（已固定）

| 决策 | 选项 | 原因 |
|------|------|------|
| 仓库形态 | 单体仓库，内部复制 AI_Group 后端包结构 | 避免多仓库 Git/CI 复杂度，专注架构学习 |
| 数据库 | PostgreSQL + SQLAlchemy 异步（asyncpg）+ alembic 迁移 | 对齐 AI_Group，所有业务表加 `tenant_id` |
| 认证 | JWT（python-jose，无状态） | 对齐 AI_Group，适合前后端分离 |
| 向量存储 | Qdrant（保留现有基础设施） | 用户选择，现有 knowledge_simple 已迁移至 Qdrant |
| 角色模型 | member（客户）/ agent（坐席）/ admin（后台管理员） | 对齐 AI_Group 客服术语，区分访客与员工 |
| 现有路由 | 并行保留（旧伴侣路由 `/api/chat/*`, `/api/sessions/*` 不删，新客服路由另起） | 便于新旧对比学习，不破坏现有功能 |
| 数据迁移 | 新表并存，旧表不迁移（ai_sessions/ai_messages 保留原样） | 降低迁移风险，新旧系统可并行运行 |
| 前端 | 先改造现有静态 HTML 作为客服聊天页，后续再接 Vue | 先验证后端对话链路，循序渐进 |
| 学生管理模块 | 保留，作为可接入的业务子系统/集成示例 | 利用现有代码，学习如何把业务系统接入客服 |

## 目标结构（src/ 下）

```
src/
  backend/
    app/
      cs/
        api/
          v1/
            member/       # 会员接口：chat, conversations, rating
            workbench/    # 坐席接口：conversations, reply, handoff
        crud/
        model/            # conversation, message, agent, rating, ...
        schema/
        service/
        socketio/         # 会员 /member，坐席 /ws
      engine/             # 领域引擎，纯 Python，无框架依赖
        nlu/              # 意图分类：业务 vs 非业务
        flow/             # 会话流程：接单、等待、转人工、关闭
        reply/            # 回复策略：知识库、固定、兜底
        state/            # 会话状态机
        policy/           # 领域边界：禁止编造，兜底话术
      admin/              # 员工 CRUD、操作日志
      integration/        # 外部适配：平台、存储
      task/               # Celery worker/beat
      plugin/             # LLM、OCR 可插拔能力
      common/             # 响应、异常、安全、上下文、事件总线、JWT 中间件
    core/                 # conf.py 配置入口
    database/             # db.py 异步引擎、alembic 迁移
    main.py               # FastAPI 应用入口
  framework/
    ai/
      aicompanion_v2/     # 保留作为参考，旧路由 /api/chat/*, /api/sessions/* 仍在此
      knowledge_simple/   # 复用：文档上传与检索（Qdrant 向量）
  shared/                 # 现有 llm.py（DeepSeek），database.py（旧同步 engine 保留）
```

## 数据模型

### 新增表（全部加 tenant_id，通过 alembic 迁移创建）

| 表 | 说明 |
|----|------|
| `tenant` | 租户：id, name, code, status, created_at |
| `cs_conversation` | 会话：id, tenant_id, member_id, agent_id, status, created_at, updated_at |
| `cs_message` | 消息：id, conversation_id, role(member/agent/ai), content, token_usage, kb_hit, created_at |
| `cs_agent` | 坐席：id, tenant_id, username, role(admin/agent), status, created_at |
| `cs_rating` | 满意度：id, conversation_id, score, comment, created_at |
| `knowledge_document` | 知识库文档：id, tenant_id, title, content, ...（复用 knowledge_simple，加 tenant_id） |
| `knowledge_chunk` | 知识库分块：id, document_id, content, embedding(Qdrant)，...（加 tenant_id） |

### 现有表（保留，不迁移）
- `ai_sessions`, `ai_messages`, `knowledge_documents`, `knowledge_chunks`（原结构，无 tenant_id）

## 接口

### 新客服接口（`/api/v1/cs/*`）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 会员发消息 | POST | `/api/v1/cs/member/chat` | 流式/非流式，知识库优先 + LLM 兜底 |
| 会员会话列表 | GET | `/api/v1/cs/member/conversations` | 我的会话列表 |
| 会员满意度 | POST | `/api/v1/cs/member/rating` | 会话满意度评价 |
| 坐席会话列表 | GET | `/api/v1/cs/workbench/conversations` | 分配给我的会话 |
| 坐席回复 | POST | `/api/v1/cs/workbench/reply` | 坐席手工回复 |
| 转人工 | POST | `/api/v1/cs/workbench/handoff` | AI 转人工 |
| 员工登录 | POST | `/api/v1/admin/auth/login` | JWT 令牌 |
| 知识库上传 | POST | `/api/v1/kb/documents` | 复用 knowledge_simple |

### 现有伴侣接口（保留，`/api/chat/*`, `/api/sessions/*`）
- 不做修改，供新旧对比学习

## 分阶段任务（可执行清单）

### Phase 1：客服对话链路 MVP
- [ ] 1.1 在 `src/backend/database/` 建立 SQLAlchemy 异步引擎（asyncpg）+ alembic 迁移环境；编写首个迁移文件创建 `tenant`, `cs_conversation`, `cs_message`, `cs_agent`, `cs_rating` 表（全部含 `tenant_id`）
- [ ] 1.2 在 `src/backend/app/common/` 新增 JWT 中间件与响应/异常统一封装
- [ ] 1.3 复用 `knowledge_simple` 的 `DocumentService.search_similar`（Qdrant）实现知识库检索（top_k + threshold，加 `tenant_id` 过滤）
- [ ] 1.4 新增 `src/backend/engine/nlu/` 意图分类器（关键词优先，LLM 兜底），区分业务领域 vs 非业务领域
- [ ] 1.5 新增 `src/backend/engine/reply/`：知识库回复、固定回复、兜底话术（"暂无资料，转人工/补充知识库"，禁止编造）
- [ ] 1.6 新增 `src/backend/app/cs/api/v1/member/`：`POST /chat`（流式/非流式），`GET /conversations`，`POST /rating`
- [ ] 1.7 全链路记录会话、消息、检索命中、token 用量（写入 `cs_conversation`/`cs_message`）
- [ ] 1.8 改造现有静态 HTML 聊天页，对接 `/api/v1/cs/member/chat`

### Phase 2：座席与后台
- [ ] 2.1 多租户权限模型：tenant + role(admin/agent/member)，JWT 鉴权中间件强制校验 `tenant_id`
- [ ] 2.2 新增 `src/backend/app/admin/`：员工 CRUD、操作日志
- [ ] 2.3 新增 `src/backend/app/cs/api/v1/workbench/`：会话列表、坐席回复、转人工
- [ ] 2.4 新增 `src/backend/app/cs/socketio/`：Socket.IO 实时推送（会员 `/member`、坐席 `/ws`）
- [ ] 2.5 新增 `src/backend/app/task/`：Celery 异步任务（会话派单、超时改派、满意度提醒）

### Phase 3：监控与运营
- [ ] 3.1 新增 metrics 聚合：会话/消息量、知识库命中率、AI 质量与成本
- [ ] 3.2 坐席工作台前端仪表盘（先沿用静态页，后续接 Vue）
- [ ] 3.3 告警规则与运营报表

## 验证步骤
1. 单元测试：检索命中/未命中分支、领域边界话术、多租户数据隔离（每条查询带 `tenant_id`）
2. 集成测试：端到端对话（会员发消息 → AI 回答 → 坐席接管 → 满意度评价）
3. Socket.IO：会员发消息后坐席端实时收到；坐席回复后会员端实时收到
4. 监控接口返回聚合数据（命中率、消息量）
5. 回归：现有 `/api/chat/*`, `/api/sessions/*` 伴侣路由仍可正常调用

## 风险与缓解
- 多租户数据隔离：中间件强制校验 `tenant_id`，每条查询必须带 `tenant` 过滤
- LLM 成本与延迟：加限流 + Redis 缓存，设置 token 上限
- 知识库质量：兜底时明确转人工，建立意图反馈机制
- 前端：先用静态 HTML 验证后端，避免前后端并行开发的复杂度
- 异步迁移：SQLAlchemy 异步与现有同步 `shared/database.py` 并存，逐步迁移，不一次性切换

## 与 AI_Group 的对照点
- `cs/model/*` → `src/backend/app/cs/model/`（conversation, message, rating 等）
- `cs/api/v1/` → `src/backend/app/cs/api/v1/`（member + workbench）
- `engine/` → `src/backend/app/engine/`（nlu, flow, reply, state, policy）
- `admin/` → `src/backend/app/admin/`
- `task/` → `src/backend/app/task/`
- `plugin/` → `src/backend/app/plugin/`
- `common/` → `src/backend/app/common/`
- `database/` + alembic → `src/backend/database/`

---
计划已就绪，可交由实施阶段执行。