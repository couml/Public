# 智慧打印机管理平台 — 交接文档

## 一、项目简介

面向企业/个人用户的智慧打印机管理平台，提供设备监控、AI 故障诊断、文件打印、驱动下载和电子文档管理一站式服务。

## 二、技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | React 18 + TypeScript + Ant Design 5 + ECharts | 端口 5173 |
| 后端 | Python FastAPI + SQLAlchemy 2.0 (async) | 端口 8000 |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） | 本地无需安装 |
| 存储 | 内存 Mock（开发）/ MinIO（生产） | 本地无需安装 |
| 缓存 | 内存 Mock（开发）/ Redis（生产） | 本地无需安装 |

## 三、环境要求

- **Node.js** ≥ 18
- **Python** ≥ 3.11
- 其他无需安装（SQLite/Redis/MinIO 均有内置 Mock）

## 四、首次启动（3 步）

### 1. 安装依赖

```bash
# 前端
cd 网站制作/frontend
npm install

# 后端
cd 网站制作/backend
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
cd 网站制作/backend
rm -f printer_platform.db
py scripts/seed.py
```

种子数据包含：3 个用户、17 台打印机（1 台在线）、10 个驱动包。

### 3. 启动服务

开两个终端：

**终端 1 — 后端：**
```bash
cd 网站制作/backend
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**终端 2 — 前端：**
```bash
cd 网站制作/frontend
npm run dev
```

浏览器访问 **http://localhost:5173** 即可。

## 五、默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | `admin123` |
| IT 运维 | `itstaff` | `it123456` |
| 普通用户 | `zhangsan` | `user1234` |

## 六、项目结构

```
├── PRD.md                    # 需求文档
├── HANDOVER.md               # 交接文档
├── .gitignore
└── 网站制作/
    ├── frontend/             # React 前端
    │   └── src/
    │       ├── api/          # Axios 客户端 + 接口调用
    │       ├── components/   # 共享组件
    │       ├── hooks/        # 自定义 Hooks
    │       ├── layouts/      # 布局（DashboardLayout、AdminLayout）
    │       ├── pages/        # 18 个页面组件
    │       ├── store/        # Zustand 状态管理
    │       ├── types/        # TypeScript 类型
    │       └── utils/        # 工具函数
    └── backend/              # Python 后端
        ├── app/
        │   ├── api/          # REST API 路由（8 组 ~70 个端点）
        │   ├── core/         # 配置、JWT、依赖注入
        │   ├── db/           # 数据库引擎 + 会话
        │   ├── models/       # SQLAlchemy ORM（12 张表）
        │   ├── schemas/      # Pydantic 请求/响应模型
        │   ├── services/     # 业务逻辑层
        │   ├── websocket/    # WebSocket 实时推送
        │   └── utils/        # MinIO Mock、Redis Mock、PDF 生成
        └── scripts/seed.py   # 数据库初始化
```

## 七、功能模块速查

| 路由 | 功能 | 说明 |
|------|------|------|
| `/dashboard` | 仪表盘 | 设备统计、状态图表、告警概览 |
| `/devices` | 设备列表 | 卡片/表格视图，品牌/状态筛选 |
| `/devices/:id` | 设备详情 | 实时状态、历史图表、告警、打印队列 |
| `/diagnosis` | AI 诊断 | 对话式故障诊断，选择打印机获取驱动推荐 |
| `/print` | 文件打印 | 上传→转换→查看→打印，完整流程 |
| `/print/history` | 打印历史 | 任务记录、统计 |
| `/drivers` | 驱动下载 | 品牌/型号搜索，HP 136a 专属页 |
| `/documents` | 文档管理 | 扫描件存档、预览、下载 |
| `/admin` | 管理后台 | 打印机/驱动/用户/日志管理 |

## 八、文件打印流程

1. **上传**：拖拽文件到上传区（图片/文本/PDF/Office 均可）
2. **转换**：点"转换"按钮，图片→PDF、文本→PDF 真实转换
3. **查看**：点"查看"按钮，浏览器新标签页预览转换后的文件
4. **打印**：选打印机，配置参数，提交到打印队列

## 九、AI 诊断说明

- 输入故障现象（如"卡纸"、"打印条纹"、"连不上"），自动匹配诊断结果
- 关联打印机后显示实时状态（在线/离线/碳粉/纸张）
- 自动推荐对应品牌型号的驱动程序
- 包含 50+ HP 错误码识别（50.x 定影、13.xx 卡纸等）

## 十、常见问题

### Q: 前端启动后无法连接后端？
确保后端已先启动在 8000 端口。前端 Vite 代理自动转发 `/api` 到后端。

### Q: 上传文件报错？
本地使用内存存储，重启后已上传文件会丢失。重新上传即可。

### Q: 设备列表只显示一台在线？
种子数据显示 1 台 HP Laser MFP 136a 在线，其余 16 台默认离线。

### Q: 数据库如何重置？
```bash
rm -f printer_platform.db && py scripts/seed.py
```

## 十一、部署信息

| 环境 | 前端 | 后端 |
|------|------|------|
| 本地开发 | `localhost:5173` | `localhost:8000` |
| 生产 | `couml.github.io/Public/` | `public-utfr.onrender.com` |

- 前端部署：GitHub Pages（Actions 自动构建）
- 后端部署：Render（免费层，首次请求需等 30-60s 唤醒）
- 部署配置：`.github/workflows/deploy-frontend.yml`
- 环境变量：`VITE_API_BASE` = 后端地址
