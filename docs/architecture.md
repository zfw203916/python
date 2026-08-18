# 架构设计文档

## 分层架构

```
┌─────────────────────────────────────────┐
│  测试用例层 (Test Cases)                │
│  unit / integration / e2e / contract    │
├─────────────────────────────────────────┤
│  业务逻辑层 (App)                       │
│  models / clients / factories           │
├─────────────────────────────────────────┤
│  框架层 (Framework)                     │
│  config / logger / client / ai          │
├─────────────────────────────────────────┤
│  基础设施层 (Infrastructure)            │
│  Docker / CI / pre-commit / Allure      │
└─────────────────────────────────────────┘
```

## 测试金字塔

```
        /\        E2E（少而精）
       /  \
      /____\
     /      \
    /________\  集成测试
   /          \
  /____________\ 单元测试（多而快）
```

## 技术选型

- Python 3.13+
- uv (包管理)
- pytest + allure
- Pydantic v2 + SQLAlchemy 2.x
- respx + httpx
- Docker + GitHub Actions
