# 智慧打印机管理平台 (Smart Printer Management Platform)

面向企业与个人用户的智慧打印机管理平台，提供设备实时监控、云端 AI 故障诊断、文件打印、驱动下载及电子文档管理一站式服务。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Ant Design 5 + ECharts |
| 后端 | Python FastAPI + SQLAlchemy 2.0 (async) |
| 数据库 | PostgreSQL 16 + Redis 7 |
| 文件存储 | MinIO |
| 实时通信 | WebSocket + Redis Pub/Sub |

## 快速启动

### 1. 启动基础设施

```bash
docker-compose up -d
```

### 2. 启动后端

```bash
cd backend
cp .env.example .env  # 编辑 .env 修改默认配置
pip install -r requirements.txt
python scripts/seed.py  # 初始化数据库和种子数据
uvicorn app.main:app --reload --port 8000
```

API 文档: http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问: http://localhost:5173

### 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| IT 运维 | itstaff | it123456 |
| 普通用户 | zhangsan | user1234 |

## 功能模块

- **仪表盘** — 设备统计、实时状态图表、告警概览
- **设备监控** — 打印机列表、实时状态推送 (WebSocket)、历史日志、告警管理
- **AI 故障诊断** — 智能对话诊断、错误码识别、维修方案推荐、PDF 报告导出
- **文件打印** — 拖拽上传、分片传输、格式转换、打印队列追踪、打印历史
- **驱动下载** — 品牌/型号搜索、多平台下载、HP 136a 专属页、安装指南
- **电子文档** — 扫描件归档、在线预览、OCR 识别、分享链接
- **管理后台** — 设备/驱动/用户/日志管理、系统统计

## 项目结构

```
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 配置、安全、依赖注入
│   │   ├── db/           # 数据库会话
│   │   ├── models/       # SQLAlchemy ORM 模型
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   ├── services/     # 业务逻辑层
│   │   ├── websocket/    # WebSocket 管理
│   │   └── utils/        # 工具函数
│   ├── alembic/          # 数据库迁移
│   └── scripts/          # 种子数据
└── frontend/
    └── src/
        ├── api/           # API 客户端
        ├── components/    # 共享组件
        ├── hooks/         # 自定义 Hooks
        ├── layouts/       # 布局组件
        ├── pages/         # 页面组件
        ├── store/         # Zustand 状态管理
        ├── types/         # TypeScript 类型
        └── utils/         # 工具函数
```
