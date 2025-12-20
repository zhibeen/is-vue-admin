# 技术框架选型

## 1. 架构模式
- **模式**: 前后端分离
- **交互方式**: RESTful API (JSON)
- **响应格式**: 统一封装格式 (Unified Response Format)
  - **结构**: `{ code: number, message: string, data: any }`
  - **code**: 0 表示成功，非 0 表示业务异常或系统错误。
  - **message**: 错误提示信息或操作结果描述。
  - **data**: 业务数据载体。

## 2. 前端 (Frontend)
- **核心框架**: [Vben Admin 5.0](https://github.com/vbenjs/vue-vben-admin)
  - **版本**: v5 (基于 Turborepo 的 Monorepo 架构)
  - **UI 组件库**: **Ant Design Vue** (深度整合版)
    - *选择理由*: 适合复杂中后台，组件丰富，Vben 官方原生支持最好。
  - **状态管理**: Pinia
  - **路由管理**: Vue Router
- **开发语言**: TypeScript
- **构建工具**: Vite
- **包管理器**: pnpm (推荐, version >= 9)
- **运行环境**: 本地 Node.js (v20+) 环境 (不使用 Docker，以便利用 HMR 热更新)

### Vben Admin 5 表格使用规范 (Grid & Table)

为避免 `proxyConfig` 的黑盒问题，推荐使用 **手动控制模式**。

#### VXE Table v4.17+ 工具栏配置规范

**重要**: VXE Table 从 v4.x 开始对 `toolbarConfig` 进行了重大更新，旧版语法已废弃。

**配置语法对照**:

| 功能 | ❌ 旧版（废弃） | ✅ 新版（推荐） |
|------|-------------|-------------|
| 刷新按钮 | `refresh: { code: 'query' }` | `refresh: true, refreshOptions: { code: 'query' }` |
| 全屏按钮 | `zoom: { code: 'fullscreen' }` | `zoom: true, zoomOptions: { code: 'fullscreen' }` |
| 自定义按钮 | `custom: { code: 'custom' }` | `custom: true, customOptions: { code: 'custom' }` |
| 列设置 | `setting: { code: 'setting' }` | `setting: true, settingOptions: { code: 'setting' }` |

**标准模板 (Standard Pattern)**:

```vue
<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getListApi } from '#/api/demo';
import { onMounted } from 'vue';
import { Button } from 'ant-design-vue';

// 1. 定义 Grid Options
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 80 },
    { field: 'name', title: '名称', minWidth: 150 },
  ],
  data: [], // 初始空数据
  
  // 分页配置
  pagerConfig: {
    enabled: true,
    currentPage: 1,
    pageSize: 20,
  },
  
  // 工具栏配置（新版语法）
  toolbarConfig: {
    // 刷新按钮：分离布尔值和配置对象
    refresh: true,                      // ✅ 是否启用
    refreshOptions: { code: 'query' },  // ✅ 配置选项
    
    // 全屏按钮
    zoom: true,
    zoomOptions: { code: 'fullscreen' },
    
    // 自定义按钮
    custom: true,
    
    // 自定义按钮插槽
    slots: {
      buttons: 'toolbar_buttons'
    }
  },
};

// 2. 初始化 Grid
const [Grid, gridApi] = useVbenVxeGrid({ 
  gridOptions,
  gridEvents: {
    toolbarToolClick: (params) => {
      if (params.code === 'query') loadData();
    }
  }
});

// 3. 数据加载函数
async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getListApi();
    // 显式更新 Grid 数据
    gridApi.setGridOptions({ data: res });
  } catch (e) {
    console.error(e);
  } finally {
    gridApi.setLoading(false);
  }
}

// 4. 挂载时触发
onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="p-4">
    <Grid>
      <!-- 自定义工具栏按钮 -->
      <template #toolbar_buttons>
        <Button type="primary" @click="handleCreate">
          新建
        </Button>
      </template>
    </Grid>
  </div>
</template>
```

**关键点**:
1.  **引入 Adapter**: 使用 `#/adapter/vxe-table`。
2.  **手动加载**: 使用 `loadData` 函数 + `gridApi.setGridOptions({ data })`。
3.  **生命周期**: 在 `onMounted` 中显式调用 `loadData()`。
4.  **刷新绑定**: 通过 `gridEvents.toolbarToolClick` 绑定刷新按钮。
5.  **新版语法**: 工具栏配置使用 `布尔值 + Options对象` 的分离模式。

**最小配置示例**:
```typescript
toolbarConfig: {
  refresh: true,
  refreshOptions: { code: 'query' },
}
```

**完整配置示例**:
```typescript
toolbarConfig: {
  refresh: true,
  refreshOptions: { code: 'query' },
  zoom: true,
  zoomOptions: { code: 'fullscreen' },
  custom: true,
  setting: true,
  settingOptions: { storage: true }, // 记住列设置
  slots: { buttons: 'toolbar_buttons' }
}
```

## 3. 后端 (Backend)
- **开发语言**: Python 3.10+
- **Web 框架**: [APIFlask](https://github.com/apiflask/apiflask)
  - 优势: 自动生成 OpenAPI 文档，内置请求验证。
  - **响应封装**: 启用 `BASE_RESPONSE_SCHEMA`，全局统一包装返回值。
- **认证方案 (Authentication)**:
  - **方式**: Bearer Token (JWT)
  - **库**: `flask-jwt-extended` + `APIFlask.HTTPTokenAuth`
  - **流程**:
    1. `/auth/login` (POST JSON) -> 获取 Access Token。
    2. 后续请求 Header 携带 `Authorization: Bearer <Token>`。
    3. 后端通过 `@auth.verify_token` 委托给 `verify_jwt_in_request` 进行校验。
  - **API 文档**:
    - 使用 APIFlask 原生 `HTTPTokenAuth`，自动生成 OpenAPI 安全定义。
    - **关键配置**: 实例化时仅使用 `HTTPTokenAuth(scheme='Bearer')`，**严禁**手动指定 `header='Authorization'` 参数。
      - *原因*: 指定 header 参数会导致 OpenAPI 将其识别为 `apiKey` 模式，Swagger UI 不会自动添加 `Bearer ` 前缀；不指定则默认为 `http/bearer` 模式，Swagger UI 会处理前缀。
- **API 路由管理 (Blueprints)**:
  - **版本控制**: 使用嵌套 Blueprint (`api_v1` 作为父级)，统一管理 `/api/v1` 前缀。
  - **目录结构**: 按业务领域模块化拆分 (Domain-Driven Design 风格)。
    ```text
    backend/app/api/
    ├── __init__.py          # 定义 api_v1 并注册子模块
    ├── auth/                # 认证模块
    │   └── routes.py
    └── product/             # 商品业务域
        ├── routes.py        # 商品核心接口 (/products)
        ├── category.py      # 分类接口 (/categories)
        └── vehicle.py       # 车型接口 (/vehiclesaux)
    ```
- **数据库**: PostgreSQL (v15+)
  - **地址**: `pgm-bp14ze6w2u23d65bco.pg.rds.aliyuncs.com`
  - **连接方式**: SQLAlchemy 2.0 ORM
- **ORM (对象关系映射)**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
  - **代码风格**: **Declarative Mapping (Mapped Class)**
  - **写法**: 使用 `Mapped[]` 和 `mapped_column()` 进行强类型定义。
  - **驱动**: `psycopg2-binary`
- **数据迁移**: Alembic (必选)
  - 作用: 管理数据库版本变更，禁止手动修改数据库表结构。

## 4. 开发环境与部署 (DevOps)
- **开发模式**:
  - **后端**: 本地 Docker (推荐) 或 本地 venv。
  - **前端**: 本地 Node 环境运行。
  - **数据库**: 阿里云 RDS (远程连接)。
- **容器化**: Docker & Docker Compose (仅后端)
  - **特点**: 多阶段构建 (Multi-stage Build)
    - `builder`: 编译依赖。
    - `final`: 基于 slim 镜像，仅复制 wheel 包，极致轻量。

### 4.1 数据库初始化与数据模拟 (Database Seeding)

为解决开发阶段数据管理混乱的问题，我们引入了统一的 CLI 命令体系。所有命令均需在 Docker 容器内执行（或在正确配置的 venv 环境下）。

#### 1. 一键初始化开发环境 (`init-dev`)
此命令用于系统冷启动，建立运行所需的“地基”。

```bash
# 在 Docker 容器内执行
docker compose exec backend flask init-dev --reset
```

- **功能**:
  1. **重置数据库** (可选 `--reset`): 删除所有表并重建（仅在非生产环境可用）。
  2. **基础数据填充**:
     - 用户与权限 (Admin/User 账号)
     - 系统字典 (SysDict)
     - 内部公司主体 (SysCompany)
     - 产品分类树 (Category)
     - 车型标准库 (Vehicle Make/Model)

#### 2. 模拟业务数据工厂 (`forge-mock`)
此命令用于开发测试阶段，生成流水线式的业务模拟数据。

```bash
# 生成少量数据 (调试 UI 用)
docker compose exec backend flask forge-mock --volume small

# 生成中等规模数据 (测试分页和性能)
docker compose exec backend flask forge-mock --volume medium
```

- **功能**:
  - 生成虚拟供应商 (Supplier)
  - 生成产品 SPU/SKU 及关联编码
  - 生成采购合同 (Contract)

#### 3. 命令文件结构
相关代码位于 `backend/app/commands/` 目录下，按业务域拆分维护。

## 5. 项目目录结构 (Monorepo)

```text
is-vue-admin/
├── backend/                   # 后端 (Python/APIFlask)
│   ├── app/
│   │   ├── __init__.py        # App 工厂函数 (配置 Auth, CORS, APIFlask, Celery, BaseResponse)
│   │   ├── celery_utils.py    # Celery 工厂函数
│   │   ├── tasks.py           # 异步任务定义
│   │   ├── logging_config.py  # 日志配置文件
│   │   ├── decorators.py      # 权限控制装饰器 (RBAC)
│   │   ├── errors.py          # 统一异常类
│   │   ├── extensions.py      # 扩展 (DB, JWT等)
│   │   ├── security.py        # 认证回调逻辑 (HTTPTokenAuth)
│   │   ├── models/            # SQLAlchemy 2.0 Models
│   │   ├── services/          # 业务逻辑层 (Service Layer)
│   │   ├── api/               # API 路由 (模块化结构)
│   │   │   ├── __init__.py    # v1 版本控制
│   │   │   ├── auth/          # 认证相关
│   │   │   └── product/       # 产品/分类/车型相关
│   │   └── schemas/           # 数据验证模式
│   ├── logs/                  # 日志文件存储 (按天切割)
│   ├── migrations/            # Alembic 迁移文件
│   ├── requirements.txt       # 依赖列表 (含 celery, redis, pytest)
│   ├── Dockerfile             # 后端镜像构建 (Multi-stage)
│   ├── config.py              # 配置类
│   └── run.py                 # 启动入口
│   ├── tests/                 # 自动化测试目录
│       ├── conftest.py
│       ├── factories.py
│       ├── api/
│       └── unit/
│
├── frontend/                  # 前端 (Vben Admin 5.0 Monorepo)
│   ├── apps/
│   │   └── web-antd/          # 主应用 (Ant Design Vue 版)
│   ├── packages/              # 共享包 (API, Hooks, Utils)
│   ├── pnpm-workspace.yaml    # 工作区配置
│   └── turbo.json             # 构建管道配置
│
├── 需求/                      # 项目文档
├── docker-compose.yml         # 后端服务编排 (Redis + Web + Worker)
├── env_config                 # 环境变量模板 (需复制为 .env)
├── README.md                  # 开发环境启动指南
└── .gitignore
```

## 6. 数据库连接配置
- **Host**: `pgm-bp14ze6w2u23d65bco.pg.rds.aliyuncs.com`
- **User**: `zhibeen`
- **Password**: `Eade2025+`
- **ORM Style**: SQLAlchemy 2.0 Mapped Class

## 7. 多设备同步与 Git 工作流
详见上文，采用 Git 同步代码，连接统一远程数据库。

## 8. 单人开发效率优化
- **前端代码自动生成**: 依据后端 OpenAPI 文档自动生成 TypeScript 接口。
- **CORS**: 后端已开启跨域。
- **工具链**: 后端使用 Ruff，前端使用 ESLint + Prettier。

## 9. API 开发规范 (API Standards)

为保证代码风格统一和文档质量，后续开发请遵循以下规范。

### 9.1 视图编写范本 (MethodView 推荐)

后续新功能模块推荐使用 **基于类的视图 (Class-Based Views)**，使用 `apiflask.views.MethodView`。这种方式更适合 RESTful 资源的管理。

**重要**: 使用 `@input` 装饰器时，建议显式指定 `arg_name`，以避免参数注入错误（特别是在测试环境下）。
例如: `@bp.input(Schema, arg_name='data')`，则处理函数必须定义 `def func(data):`。

**统一响应 (Base Response) 与返回值规范**:
后端已启用全局 `BASE_RESPONSE_SCHEMA` (结构: `{ code: 0, message: "success", data: ... }`)。为避免 APIFlask 抛出 `RuntimeError`，视图函数的返回值必须遵循以下严格规范：

1.  **返回字典 (Dict)**: **必须**手动包装在 `data` 键中。
    *   *错误*: `return {'token': '...'}` -> 导致 500 错误。
    *   *正确*: `return {'data': {'token': '...'}}`
2.  **返回模型对象 (Model Instance)**: **直接返回**对象，无需包装。框架会自动序列化并放入 `data`。
    *   *正确*: `return user_model`
3.  **返回列表 (List)**: **直接返回**列表，无需包装。
    *   *正确*: `return [user1, user2]`
4.  **无内容/删除操作**: 建议返回 `None` (默认 200 OK)，框架会自动生成 `{ code: 0, message: 'success', data: null }`。
    *   *避免*: `return '', 204` (这会导致前端收不到标准 JSON 结构，可能引发 JS 错误)。

**范本代码**:

```python
from apiflask import APIBlueprint, Schema
from apiflask.views import MethodView
from apiflask.fields import String, Integer
from app.extensions import db
from app.security import auth

# 1. 定义 Blueprint
demo_bp = APIBlueprint('demo', __name__, url_prefix='/demo', tag='DemoResource')

# 2. 定义 MethodView
class DemoListAPI(MethodView):
    # 统一应用装饰器 (如认证)
    decorators = [demo_bp.auth_required(auth)]
    
    @demo_bp.doc(summary='获取列表', description='获取 Demo 资源列表')
    @demo_bp.output(DemoSchema(many=True))
    def get(self):
        """List items"""
        # 情况 3: 直接返回列表，框架自动包装
        return []

    @demo_bp.doc(summary='创建资源', description='创建新的 Demo 资源')
    @demo_bp.input(DemoSchema, arg_name='data') # 显式指定参数名
    @demo_bp.output(DemoSchema, status_code=201)
    def post(self, data): # 参数名与 arg_name 一致
        """Create item"""
        # 情况 1 (如果返回 dict): 必须手动包装 data
        # return {'data': data} 
        
        # 情况 2 (如果返回 Model): 直接返回对象
        return data

class DemoItemAPI(MethodView):
    decorators = [demo_bp.auth_required(auth)]

    @demo_bp.doc(
        summary='获取详情', 
        description='根据 ID 获取资源详情'
    )
    @demo_bp.output(DemoSchema)
    def get(self, item_id):
        """Get item"""
        return {}

    @demo_bp.doc(summary='更新资源')
    @demo_bp.input(DemoSchema)
    @demo_bp.output(DemoSchema)
    def put(self, item_id, data):
        """Update item"""
        return data

    @demo_bp.doc(summary='删除资源')
    def delete(self, item_id):
        """Delete item"""
        # 情况 4: 返回 None (200 OK)，框架生成标准空响应 {code: 0, data: null}
        return None
```

### 9.2 文档注释要求 (OpenAPI)
所有 API 方法必须包含 `@doc` 装饰器，以生成清晰的 Swagger 文档。

- **Summary**: 简短的中文标题 (e.g. `summary='获取商品列表'`)。
- **Description**: 详细的功能描述，包含业务逻辑说明。

### 9.3 Schema 定义要求
所有 Marshmallow/APIFlask Schema 字段必须包含 `metadata` 用于文档展示。

```python
name = String(
    required=True, 
    metadata={'description': '商品名称', 'example': 'iPhone 15'}
)
```

## 10. 后端代码优化规范 (Backend Optimization Standards)

为保证系统的高性能和可维护性，必须遵循以下优化规范。

### 10.1 Service 层模式 (Business Logic Layer)
**原则**: 禁止在 `routes.py` 中编写复杂的业务逻辑（如事务控制、复杂计算、多表操作）。所有业务逻辑必须封装在 `app/services/` 目录下。

**结构**:
- `routes.py`: 仅负责请求参数解析、调用 Service、返回响应。
- `services/*.py`: 负责具体的业务逻辑、数据库操作、异常抛出。

**示例**:
```python
# services/product_service.py
class ProductService:
    def create_product(self, data):
        # 业务逻辑...
        return product
```

### 10.2 数据库查询优化 (N+1 Problem)
**原则**: 严禁在循环中进行数据库查询。必须使用 SQLAlchemy 的 Eager Loading 机制。

**方案**:
- 使用 `selectinload` 加载一对多/多对多关联。
- 使用 `joinedload` 加载多对一/一对一关联。

**示例**:
```python
stmt = select(Product).options(selectinload(Product.category))
```

### 10.3 分页与搜索规范 (Pagination & Search)
**原则**: 列表接口必须支持分页和通用搜索，禁止全量返回。

**方案**:
- **Schema**: 使用 `PaginationQuerySchema` 接收 `page`, `per_page`, `q` (关键词), `sort` (排序)。
- **Service**: 实现通用过滤逻辑，支持模糊搜索 (ilike) 和动态排序。
- **Response**: 使用 `PaginationSchema` 统一返回结构。

### 10.4 统一异常处理 (Error Handling)
**原则**: 业务层使用 `app.errors.BusinessError` 抛出异常，由框架统一捕获，禁止在视图层随意 `abort` 且不记录日志。全局 `error_processor` 会将异常统一包装为 `{code: status, message: msg, data: detail}` 格式。

### 10.5 权限控制规范 (Permission-Based Access Control)
**原则**: 采用**RBAC (Role-Based Access Control)** 模型进行功能控制，配合**数据权限 (Data Permission)** 实现细粒度的数据可见性控制。

#### 10.5.1 功能权限 (Functional Permission)
- **模型设计**:
  - `User` <-> `Role` <-> `Permission` (Many-to-Many)
  - `Permission` 包含结构化字段: `module`, `resource`, `action` (e.g., `product:view`).
- **鉴权方式**:
  - 后端: `@permission_required('product:create')`
  - 前端: `v-auth="'product:create'"`

#### 10.5.2 数据权限 (Data Permission)
为了满足复杂的企业级数据隔离需求（如：查看本人数据 vs 查看部门数据 vs 查看特定人数据），我们设计了一套**分级数据权限体系**。

- **架构设计**: **4层结构控制**
  1.  **L1 权限大类 (Category)**: 业务顶层分类 (e.g., SKU数据权限, 单据数据权限)。包含业务解释说明。
  2.  **L2 业务模块 (Module)**: 逻辑分组 (e.g., 产品, 仓库)。
  3.  **L3 功能资源 (Resource)**: 具体的控制点 (e.g., 库存明细, 批次流水)。
  4.  **L4 权限范围 (Scope)**: 可见性策略 (`all`: 全部可见, `custom`: 权限人可见)。

- **核心模型**:
  - **`DataPermissionMeta`**: 存储权限树结构 (Category -> Module -> Resource) 及描述信息。
  - **`RoleDataPermission`**: 存储角色配置。
    - `target_user_ids`: 在该大类下选中的“权限人”列表 (e.g., `[user1, user2]`)。
    - `resource_scopes`: 各功能点的开关状态 (e.g., `{ "warehouse:stock": "custom" }`)。

- **交互逻辑**:
  - **统一设置权限人**: 在 L1 大类下统一选择“权限人”集合。
  - **逐行控制开关**: 在 L3 功能点上决定是否应用该“权限人”集合。

- **后端鉴权 (Filter)**:
  - Service 层查询时调用 `apply_data_permission(query, resource, category)`。
  - 自动根据配置拼接 SQL: `WHERE owner_id IN (...)` 或 `1=0`。

#### 10.5.3 字段权限 (Field Permission / Column-Level Security)
针对敏感数据的列级控制（如：采购成本、供应商电话），采用了**基于 Schema 的自动切面拦截架构**，实现业务代码零侵入。

**1. 核心设计思想**
- **零侵入 (Zero Intrusion)**: 业务逻辑层（Service）和数据模型层（Model）无需感知权限逻辑，仅在序列化层（Schema）通过 Mixin 自动处理。
- **AOP 切面**: 利用 Marshmallow 的 `dump` 过程作为切面，拦截所有出站数据。

**2. 架构详情**

- **数据库模型**:
  - `FieldPermissionMeta`: 定义系统中有哪些敏感字段（通过 CLI 扫描 Schema 自动生成）。
    - 关键字段: `module` (模块), `field_key` (唯一标识, 如 `product:cost_price`), `label` (显示名)。
  - `RoleFieldPermission`: 定义角色对字段的可见性。
    - 关键字段: `role_id`, `field_key`, `is_visible` (Boolean), `condition` (Enum: `none`, `follower` 等)。

- **Schema 定义规范**:
  开发人员只需在 APIFlask/Marshmallow Schema 中通过 `metadata` 标记敏感字段。
  ```python
  class ProductSchema(FieldPermissionMixin, Schema): # 1. 继承 Mixin
      id = Integer()
      name = String()
      # 2. 标记敏感字段
      cost_price = String(metadata={'permission_key': 'product:cost_price', 'label': '采购成本'}) 
  ```

- **执行流程 (Pipeline)**:
  1.  **Service 层**: 返回完整的 ORM 对象 (包含敏感数据)。
  2.  **Schema Dump**: 框架调用 `schema.dump(obj)`。
  3.  **Mixin 拦截**: `FieldPermissionMixin` 重写 `dump` 或 `post_dump`。
  4.  **权限判定**:
      - 获取当前用户角色。
      - 查询 `RoleFieldPermission` 缓存。
      - **静态判断**: `is_visible` 为 False -> 执行脱敏。
      - **动态判断**: `condition == 'follower'` -> 检查 `obj.follower_id == current_user.id`。
  5.  **脱敏执行**:
      - **掩码 (Masking)**: 将值替换为 `******` (保留 Key，前端显示星号)。
      - **隐藏 (Hidden)**: 直接从字典中 `pop` 掉 Key (前端表格该列为空)。
  6.  **Response**: 返回处理后的 JSON。

**3. 前端适配方案**

- **方案 A (当前默认 - 自适应)**:
  - 利用 Ant Design Vue Table 的特性。
  - 如果后端删除了 Key，表格该单元格自动为空。
  - 如果后端返回 `***`，表格直接显示文本。
  - *优势*: 前端零开发，完全由后端控制。

- **方案 B (进阶 - 动态列)**:
  - *场景*: 如果需要让“无权限的列”直接从表格中消失，而不是显示空白或星号。
  - *实现*: 使用 `useTablePermission(schemaKey)` Hook。在渲染 Table 前，先请求后端获取当前用户的“可见字段列表”，动态过滤 `columns` 数组。

## 11. 日志与监控系统 (Logging & Monitoring)

我们采用了结构化日志（JSON）+ 文件轮转的方案，既方便开发调试，又无缝对接云端日志服务。

### 11.1 本地日志策略
- **开发环境 (stdout)**: 控制台输出彩色日志，格式易读。
- **生产环境 (file)**: 输出 JSON 格式日志到 `backend/logs/app.log`。
  - **自动切割**: 每天午夜自动生成新文件 (e.g., `app.log.2023-10-27`)。
  - **保留周期**: 本地保留 30 天，过期自动删除。
  - **包含字段**: `timestamp`, `level`, `module`, `message`, `user_id`, `request_id`, `duration` 等。

### 11.2 阿里云日志服务 (SLS) 对接指南
生产环境下，推荐使用 **Logtail 采集** 模式，对业务代码**零侵入**。

#### 步骤一：准备工作
1. 在阿里云控制台开通 **日志服务 (SLS)**。
2. 创建 **Project** (e.g., `is-admin-prod`) 和 **Logstore** (e.g., `backend-logs`)。
3. 在 ECS 服务器上安装 **Logtail** (阿里云提供一键安装命令)。

#### 步骤二：配置 Logtail 采集配置
1. 进入 Logstore -> 数据接入 -> **JSON - 文本日志**。
2. **日志路径**: 填写容器挂载到宿主机的日志目录，例如 `/var/log/is-admin/backend/*.log`。
   - *注意*: 确保 Docker 启动时使用了 Volume 挂载: `-v /host/logs:/app/logs`。
3. **模式**: 选择 **JSON 模式**。Logtail 会自动解析 JSON 字段。
4. **时间解析**: 选择 `timestamp` 字段作为日志时间。

#### 步骤三：查询与分析
配置完成后，日志会自动上传至 SLS。你可以：
- 使用 SQL 语法查询：`status > 500 | select count(1) as error_count`
- 根据 `request_id` 全链路追踪问题。
- 设置告警规则（如每分钟 Error 超过 10 个发送钉钉通知）。

## 12. 部署与架构演进路线 (Deployment Roadmap)

基于项目发展阶段，我们制定了分阶段的部署策略。

### 12.1 阶段一：本地开发 (Local Dev)
- **场景**: 单人/小团队功能迭代。
- **架构**:
  - PC 运行后端 (Docker Compose) + 前端 (Node)。
  - 数据库连接远程阿里云 RDS (开发库)。
  - **启动方式**: `flask run --debug` (热重载，通过 docker-compose.yml 覆盖默认 CMD)。
- **默认账号**:
  - **用户名**: `admin`
  - **密码**: `password` (由 `seed-db` 命令生成，角色名为 "管理员")
- **关键技术**: Docker Volume 挂载源码。
- **数据持久性**:
  - 由于使用了**独立的阿里云 RDS**，开发环境采用了**计算与存储分离**的架构。
  - **Docker 容器重建** (`docker compose down && up`) 仅重置计算实例（代码运行环境），**不会影响**数据库中的业务数据。
- **工作流推荐**:
  - **修改代码 (Python)**: 直接保存，Flask 热重载自动生效 (无需重启)。
  - **修改依赖/配置 (requirements.txt, Dockerfile)**: 执行 `docker compose down && docker compose up --build -d`。这是合理且正确的方案，确保环境纯净且数据安全。

### 12.2 阶段二：首次上线 (Initial Launch)
- **场景**: 内部试用 / 小规模公测。
- **架构**: **单体 ECS (云服务器)**。
  - 购买一台 ECS (e.g. 2核4G)。
  - 部署方式: `Docker Compose`。
    - 后端服务 (使用 Dockerfile 默认的 **Gunicorn** 启动，高性能)。
    - Nginx (反向代理 + 静态资源)。
    - Redis (缓存 & 消息队列)。
  - 数据库: 继续使用阿里云 RDS (生产库)。
  - 异步队列: 使用 Docker Compose 中的 `redis` 和 `celery_worker` 服务。
- **优势**: 部署简单，成本低，与开发环境高度一致，排查问题方便。

### 12.3 阶段三：规模化扩展 (Scaling Phase)
- **场景**: 业务增长，流量增加，对高可用有要求。
- **架构**: **阿里云 SAE (Serverless) + 独立 RDS/Redis**。
  - **应用层**: 迁移至 **SAE (Serverless App Engine)**。
    - **Web 实例**: 配置 Gunicorn 启动，处理 API 请求。
    - **Worker 实例**: 独立部署，配置 `celery worker` 启动，处理异步任务。
    - 优势: 免运维、秒级自动扩缩容、灰度发布。
  - **数据层**: 独立的 RDS PostgreSQL (主备高可用) + 云数据库 Redis。
  - **静态资源**: 前端构建产物部署至 **OSS + CDN**。
- **优势**: 极致弹性，运维成本极低，稳定性高。

## 13. 自动化测试体系 (Testing Strategy)

为保证代码质量和重构安全性，项目引入了完整的自动化测试体系。

### 13.1 技术栈
- **核心框架**: `pytest`
- **数据工厂**: `factory_boy` (基于 SQLAlchemy 模型自动生成测试数据) + `Faker`
- **覆盖率**: `pytest-cov`
- **Flask 集成**: `pytest-flask`

### 13.2 测试架构与模式
- **数据库策略**: 使用 **SQLite 内存数据库** (`sqlite:///:memory:`) 进行极速测试。
- **事务回滚**: 每个测试用例运行在独立的数据库事务中，测试结束后自动回滚，保证环境纯净。
- **JSONB 兼容**: 通过 `conftest.py` 中的 Monkey Patch，让 SQLite 能够处理 PostgreSQL 的 `JSONB` 类型（自动降级为 `JSON`）。
- **目录结构**:
  ```text
  backend/tests/
  ├── conftest.py          # 全局 Fixture (App, Client, DB Session, AdminUser)
  ├── factories.py         # 数据工厂 (UserFactory, ProductFactory)
  ├── api/                 # 集成测试 (测试 API 接口权限、逻辑)
  └── unit/                # 单元测试 (测试 Service 层复杂算法)
  ```

### 13.3 常用命令
- **运行所有测试**:
  ```bash
  # 在 Docker 中运行 (推荐)
  docker compose exec backend env PYTHONPATH=/app pytest
  ```
- **运行特定测试文件**:
  ```bash
  docker compose exec backend env PYTHONPATH=/app pytest tests/api/test_auth.py
  ```
- **查看覆盖率报告**:
  ```bash
  docker compose exec backend env PYTHONPATH=/app pytest --cov=app
  ```

## 14. 异步任务架构 (Async Task Queue)

为解决耗时操作（如导出、发邮件）导致的请求超时问题，引入了 Celery 分布式任务队列。

### 14.1 架构组件
- **Broker**: **Redis** (消息中间件，负责存取任务)。
- **Worker**: **Celery Worker** (后台进程，负责执行任务)。
- **Producer**: **Flask API** (生产者，负责派发任务)。

### 14.2 代码实现
- **任务定义**: `backend/app/tasks.py` 使用 `@shared_task`。
- **任务调用**: `task.delay(arg1, arg2)`。
- **初始化**: 在 `create_app` 中通过 `celery_init_app` 绑定 Flask 上下文。

## 15. 待实施架构演进 (Future Roadmap - Pending Implementation)

本章节列出的方案目前**尚未实装**。这些是为未来大规模业务场景准备的架构升级计划，属于企业级标准的高级特性。

### 15.1 API 限流 (Rate Limiting)
- **当前状态**: 未实施
- **实施时机**:
  - 当 API 每日调用量超过 10万次。
  - 或遭遇第一次 CC 攻击/爬虫暴力破解时。
  - 或系统开放公网注册，存在被恶意刷库风险时。
- **技术方案**:
  - **库**: `Flask-Limiter`
  - **存储**: 复用现有的 Redis。
  - **代码示例**:
    ```python
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri="redis://redis:6379/0"
    )
    
    @auth_bp.route('/login', methods=['POST'])
    @limiter.limit("5 per minute") # 针对登录接口严格限流
    def login(): ...
    ```

### 15.2 软删除 (Soft Delete)
- **当前状态**: 未实施 (目前采用物理删除)
- **实施时机**:
  - 正式上线运营后，需要保留数据审计痕迹时。
  - 防止客服/运营人员误操作导致数据永久丢失时。
- **技术方案**:
  - **Mixin 设计**:
    ```python
    class SoftDeleteMixin:
        deleted_at = db.Column(db.DateTime, nullable=True)
        
        def delete(self):
            self.deleted_at = datetime.now()
            db.session.add(self)
            
        @classmethod
        def query_active(cls):
            return cls.query.filter_by(deleted_at=None)
    ```
  - **迁移工作**: 需要为所有表添加 `deleted_at` 字段 (Alembic 迁移)。

### 15.3 代码质量门禁 (Pre-commit Hooks)
- **当前状态**: 未实施 (仅建议本地安装 Ruff)
- **实施时机**:
  - 开发团队扩充至 2 人以上时。
  - 代码风格开始出现不一致（如引号混用、缩进混乱）时。
- **技术方案**:
  - **工具**: `pre-commit`
  - **配置**: `.pre-commit-config.yaml`
    ```yaml
    repos:
      - repo: https://github.com/astral-sh/ruff-pre-commit
        rev: v0.1.0
        hooks:
          - id: ruff
            args: [ --fix, --exit-non-zero-on-fix ]
    ```

### 15.4 全链路追踪 (Observability / Distributed Tracing)
- **当前状态**: 未实施 (仅有基础 Request ID)
- **实施时机**:
  - 引入微服务架构或调用链路变得极度复杂时。
  - 发现某些异步任务 (Celery) 报错无法定位是由哪个 Web 请求触发时。
- **技术方案**:
  - **Request ID 透传**:
    1. Flask Middleware 生成 `X-Request-ID`。
    2. 存入 `flask.g`。
    3. 调用 Celery 时: `task.apply_async(..., headers={'X-Request-ID': g.request_id})`。
    4. Celery Worker 读取 Header 并注入日志上下文。

### 15.5 生产环境数据初始化策略 (Production Seeding Strategy)
- **当前状态**: 开发环境混用初始化与模拟数据
- **未来规划**:
  - **分离基础数据**: 将 `init-dev` 中的核心基础数据（如：系统字典、基础权限、行政区划、初始管理员）提取为独立的 `flask init-prod` 命令。
  - **版本化数据迁移**:
    - 数据库结构变更严格通过 Alembic (`flask db upgrade`) 管理。
    - 关键的基础数据变更（如新增系统字典项）应编写为 Alembic 的 Data Migration 脚本，随代码版本自动应用。
  - **预置数据加载器**:
    - 对于某些只读的静态大数据（如标准车型库），考虑在生产部署时通过 SQL 文件直接导入，而非 ORM 逐条插入，以提高效率。
