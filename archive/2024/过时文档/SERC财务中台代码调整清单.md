# SERC财务中台系统 - 代码调整清单

> **文档版本**: v1.1  
> **创建日期**: 2025-12-19  
> **最后更新**: 2025-12-19  
> **依据文档**: 《SERC财务中台实施路线图》  
> **代码库位置**: `D:\jzb_program\is-vue-admin`

---

## 一、概述

本文档详细列出了基于《SERC财务中台实施路线图》需要调整、扩展或新建的代码文件，按6个实施阶段组织。

### 1.1 调整类型说明

- 🆕 **新建** - 需要新建的文件
- 🔧 **调整** - 需要修改的现有文件
- ✅ **无需调整** - 现有文件无需改动
- 🗑️ **废弃** - 逐步废弃的文件（向后兼容）
- ⏸️ **暂缓** - 暂不实施的功能

### 1.2 重要业务约束

> ⚠️ **关键说明**：
> 
> 1. **物流费用手工录入**
>    - 物流服务商（海运、空运、陆运等）**没有API接口**
>    - 头程费用（运费、保险费、操作费等）采用**手工录入**方式
>    - 不涉及自动对账功能，对账单由财务人员根据服务商提供的账单手工核对后录入系统
> 
> 2. **对接API功能暂缓**
>    - "自动对接物流服务商API"功能**暂缓开发**
>    - "自动获取费用"功能**暂缓开发**
>    - 未来如有物流服务商提供API，可在后续版本扩展
> 
> 3. **核心实施范围**
>    - 物流服务商主数据管理（手工维护）
>    - 物流服务明细录入（手工填写预估/实际费用）
>    - 物流对账单生成（基于已录入的费用）
>    - 凭证上传（服务凭证、付款凭证手工上传）
>    - 付款管理（进入付款池统一调度）

---

## 二、阶段0：准备阶段（文档梳理）

### 2.1 详细设计文档（需新建）

| 序号 | 文档名称 | 路径 | 说明 |
|------|---------|------|------|
| 1 | 物流服务商与对账管理详细设计 | `开发设计文档/物流模块/物流服务商与对账管理设计.md` | 数据模型、API接口、业务流程 |
| 2 | 凭证管理系统详细设计 | `开发设计文档/物流模块/凭证管理系统设计.md` | 凭证中心架构、上传归档流程 |
| 3 | 付款池扩展设计 | `开发设计文档/财务模块/付款池扩展设计.md` | 付款池类型扩展、统一调度 |

---

## 三、阶段1：基础数据模型（2-3天）

### 3.1 后端 - 数据库迁移

#### 📂 `backend/migrations/versions/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `[timestamp]_add_logistics_providers_and_document_center.py` | 🆕 新建 | 创建物流服务商表和凭证管理中心表 |

**迁移内容**：

1. **创建 `logistics_providers` 表**
   ```python
   # 核心字段
   - id (主键)
   - provider_name (服务商名称)
   - provider_code (服务商编码, unique)
   - service_type (服务类型: 陆运/海运/空运/清关/派送)
   - payment_method (付款方式: 即付/预付/后付)
   - settlement_cycle (结算周期: 即时/周结/月结)
   - contact_name (联系人)
   - contact_phone (联系电话)
   - contact_email (邮箱)
   - bank_name (开户银行)
   - bank_account (银行账号)
   - bank_account_name (账户名称)
   - service_areas (服务区域, ARRAY)
   - is_active (启用状态, default=True)
   - notes (备注)
   - created_at, updated_at
   ```

2. **创建 `document_center` 表**（通用凭证管理）
   ```python
   # 核心字段
   - id (主键)
   - business_type (业务类型: logistics/purchase/customs/payment)
   - document_type (凭证类型: 运单/提单/清关单/发票/报关单/付款单等)
   - document_category (文档分类: 服务凭证/付款凭证/合同凭证等)
   - business_id (业务单据ID, 外键根据business_type动态关联)
   - business_no (业务单据编号, 冗余字段方便查询)
   - file_name (文件名)
   - file_path (文件路径, NAS或OSS)
   - file_size (文件大小, bytes)
   - file_type (文件扩展名)
   - file_url (可访问URL, 预签名URL)
   - uploaded_by_id (上传人ID, 外键 → users)
   - uploaded_at (上传时间)
   - audit_status (审核状态: pending/approved/rejected)
   - audited_by_id (审核人ID)
   - audited_at (审核时间)
   - audit_notes (审核备注)
   - archived (是否已归档, default=False)
   - archive_path (归档路径)
   - archived_at (归档时间)
   - created_at, updated_at
   ```

**索引**：
- `logistics_providers`: `provider_code` (unique), `provider_name`, `is_active`
- `document_center`: 
  - `business_type + business_id` (复合索引)
  - `business_no`
  - `uploaded_by_id`
  - `audit_status`
  - `archived`

---

### 3.2 后端 - Models

#### 📂 `backend/app/models/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `logistics_provider.py` | 🆕 新建 | 物流服务商模型 |

**新建内容**：
```python
"""
物流服务商模型 (LogisticsProvider)
用于管理物流服务商主数据，区别于商品供应商
"""
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Boolean, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db

class LogisticsServiceType(str, Enum):
    """物流服务类型"""
    DOMESTIC_TRUCKING = 'domestic_trucking'    # 国内卡车运输
    INTERNATIONAL_SEA = 'international_sea'    # 国际海运
    INTERNATIONAL_AIR = 'international_air'    # 国际空运
    CUSTOMS_CLEARANCE = 'customs_clearance'    # 清关服务
    DESTINATION_DELIVERY = 'destination_delivery'  # 目的国派送

class PaymentMethodType(str, Enum):
    """付款方式"""
    PREPAID = 'prepaid'      # 预付
    IMMEDIATE = 'immediate'  # 即付
    POSTPAID = 'postpaid'    # 后付

class SettlementCycle(str, Enum):
    """结算周期"""
    IMMEDIATE = 'immediate'  # 即时结算
    WEEKLY = 'weekly'        # 周结
    MONTHLY = 'monthly'      # 月结

class LogisticsProvider(db.Model):
    """物流服务商表"""
    __tablename__ = "logistics_providers"
    
    # ... 字段定义（与迁移文件一致）
```

---

#### 📂 `backend/app/models/document/`（新建目录）

| 文件 | 类型 | 说明 |
|------|------|------|
| `__init__.py` | 🆕 新建 | 初始化文件 |
| `document_center.py` | 🆕 新建 | 凭证管理中心模型 |

**新建内容**：
```python
"""
凭证管理中心模型 (DocumentCenter)
通用的业务凭证管理，支持物流/采购/报关/付款四大类凭证
"""
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class BusinessType(str, Enum):
    """业务类型"""
    LOGISTICS = 'logistics'      # 物流业务
    PURCHASE = 'purchase'        # 采购业务
    CUSTOMS = 'customs'          # 报关业务
    PAYMENT = 'payment'          # 付款业务

class DocumentCategory(str, Enum):
    """文档分类"""
    SERVICE_VOUCHER = 'service_voucher'    # 服务凭证
    PAYMENT_VOUCHER = 'payment_voucher'    # 付款凭证
    CONTRACT_VOUCHER = 'contract_voucher'  # 合同凭证
    INVOICE_VOUCHER = 'invoice_voucher'    # 发票凭证
    CUSTOMS_VOUCHER = 'customs_voucher'    # 报关凭证

class AuditStatus(str, Enum):
    """审核状态"""
    PENDING = 'pending'      # 待审核
    APPROVED = 'approved'    # 已审核
    REJECTED = 'rejected'    # 已驳回

class DocumentCenter(db.Model):
    """凭证管理中心表"""
    __tablename__ = "document_center"
    
    # ... 字段定义（与迁移文件一致）
```

---

### 3.3 后端 - Schemas

#### 📂 `backend/app/schemas/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `logistics_provider.py` | 🆕 新建 | 物流服务商序列化Schema |

**新建内容**：
```python
from apiflask import Schema
from apiflask.fields import String, Boolean, List as ListField, Integer, DateTime
from marshmallow import validates, ValidationError

class LogisticsProviderSchema(Schema):
    """物流服务商输出Schema"""
    id = Integer(dump_only=True)
    provider_name = String(required=True, metadata={'description': '服务商名称', 'example': '顺丰速运'})
    provider_code = String(required=True, metadata={'description': '服务商编码', 'example': 'SF001'})
    service_type = String(metadata={'description': '服务类型'})
    # ... 其他字段

class LogisticsProviderCreateSchema(Schema):
    """物流服务商创建Schema"""
    provider_name = String(required=True)
    provider_code = String(required=True)
    # ...

class LogisticsProviderUpdateSchema(Schema):
    """物流服务商更新Schema"""
    provider_name = String()
    # ...
```

---

#### 📂 `backend/app/schemas/document/`（新建目录）

| 文件 | 类型 | 说明 |
|------|------|------|
| `__init__.py` | 🆕 新建 | 初始化文件 |
| `document.py` | 🆕 新建 | 凭证管理Schema |

---

### 3.4 后端 - Services

#### 📂 `backend/app/services/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `logistics_provider_service.py` | 🆕 新建 | 物流服务商业务逻辑 |

**新建内容**：
```python
"""
物流服务商服务层
处理物流服务商的CRUD业务逻辑
"""
from app.models.logistics.logistics_provider import LogisticsProvider
from app.extensions import db
from app.errors import BusinessError

class LogisticsProviderService:
    """物流服务商业务逻辑类"""
    
    @staticmethod
    def create_provider(data: dict, created_by: int):
        """创建物流服务商"""
        # 检查编码是否重复
        if LogisticsProvider.query.filter_by(provider_code=data['provider_code']).first():
            raise BusinessError('服务商编码已存在', code=400)
        
        provider = LogisticsProvider(**data)
        db.session.add(provider)
        db.session.commit()
        return provider
    
    @staticmethod
    def get_provider_by_id(provider_id: int):
        """根据ID获取服务商"""
        return LogisticsProvider.query.get(provider_id)
    
    # ... 其他方法
```

---

#### 📂 `backend/app/services/document/`（新建目录）

| 文件 | 类型 | 说明 |
|------|------|------|
| `__init__.py` | 🆕 新建 | 初始化文件 |
| `document_service.py` | 🆕 新建 | 凭证管理业务逻辑 |
| `archive_service.py` | 🆕 新建 | 归档服务（阶段3实现） |

---

### 3.5 后端 - API Routes

#### 📂 `backend/app/api/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `logistics_provider_routes.py` | 🆕 新建 | 物流服务商API路由 |

**新建内容**：
```python
"""物流服务商API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from app.security import auth
from app.decorators import permission_required
from app.schemas.logistics.logistics_provider import (
    LogisticsProviderSchema,
    LogisticsProviderCreateSchema,
    LogisticsProviderUpdateSchema
)
from app.services.logistics.logistics_provider_service import LogisticsProviderService

logistics_provider_bp = APIBlueprint(
    'logistics_providers', 
    __name__, 
    url_prefix='/logistics-providers', 
    tag='物流服务商管理'
)

class LogisticsProviderListAPI(MethodView):
    """物流服务商列表API"""
    decorators = [logistics_provider_bp.auth_required(auth)]
    
    @logistics_provider_bp.doc(summary='获取物流服务商列表')
    @logistics_provider_bp.output(LogisticsProviderSchema(many=True))
    def get(self):
        """获取列表"""
        # ...
    
    @logistics_provider_bp.doc(summary='创建物流服务商')
    @logistics_provider_bp.input(LogisticsProviderCreateSchema, arg_name='data')
    @logistics_provider_bp.output(LogisticsProviderSchema, status_code=201)
    @permission_required('logistics:provider:create')
    def post(self, data):
        """创建服务商"""
        # ...

# ... 其他API
```

---

#### 📂 `backend/app/api/document/`（新建目录）

| 文件 | 类型 | 说明 |
|------|------|------|
| `__init__.py` | 🆕 新建 | 初始化文件 |
| `document_routes.py` | 🆕 新建 | 凭证管理API路由 |

---

### 3.6 后端 - 注册Blueprint

#### 📂 `backend/app/api/__init__.py`

| 文件 | 类型 | 说明 |
|------|------|------|
| `__init__.py` | 🔧 调整 | 注册新的Blueprint |

**调整内容**：
```python
# 现有代码
from app.api.logistics.routes import logistics_bp

# 新增导入
from app.api.logistics.logistics_provider_routes import logistics_provider_bp
from app.api.document.document_routes import document_bp

def register_blueprints(api_v1):
    """注册所有Blueprint"""
    # 现有
    api_v1.register_blueprint(logistics_bp)
    
    # 新增
    api_v1.register_blueprint(logistics_provider_bp)  # 物流服务商
    api_v1.register_blueprint(document_bp)            # 凭证管理
    # ...
```

---

### 3.7 前端 - API封装

#### 📂 `frontend/apps/web-antd/src/api/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `logistics-provider.ts` | 🆕 新建 | 物流服务商API封装 |

**新建内容**：
```typescript
import { request } from '@vben/request';

export interface LogisticsProvider {
  id: number;
  provider_name: string;
  provider_code: string;
  service_type: string;
  payment_method: string;
  settlement_cycle: string;
  contact_name?: string;
  contact_phone?: string;
  bank_name?: string;
  bank_account?: string;
  is_active: boolean;
  created_at: string;
}

export interface LogisticsProviderCreate {
  provider_name: string;
  provider_code: string;
  service_type: string;
  payment_method: string;
  settlement_cycle: string;
  // ...
}

/**
 * 获取物流服务商列表
 */
export function getLogisticsProviders(params?: any) {
  return request<LogisticsProvider[]>({
    url: '/api/v1/logistics-providers',
    method: 'GET',
    params,
  });
}

/**
 * 创建物流服务商
 */
export function createLogisticsProvider(data: LogisticsProviderCreate) {
  return request<LogisticsProvider>({
    url: '/api/v1/logistics-providers',
    method: 'POST',
    data,
  });
}

// ... 其他API
```

---

#### 📂 `frontend/apps/web-antd/src/api/document/`（新建目录）

| 文件 | 类型 | 说明 |
|------|------|------|
| `document.ts` | 🆕 新建 | 凭证管理API封装 |

---

### 3.8 前端 - 页面组件

#### 📂 `frontend/apps/web-antd/src/views/logistics/provider/`（新建目录）

| 文件 | 类型 | 说明 |
|------|------|------|
| `index.vue` | 🆕 新建 | 物流服务商列表页 |
| `components/ProviderFormModal.vue` | 🆕 新建 | 服务商创建/编辑弹窗 |

**新建内容**（`index.vue`）：
```vue
<script setup lang="ts">
/**
 * 物流服务商管理页面
 */
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { 
  getLogisticsProviders, 
  deleteLogisticsProvider 
} from '#/api/logistics/logistics-provider';
import { onMounted, ref } from 'vue';
import ProviderFormModal from './components/ProviderFormModal.vue';

// Grid配置
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 80 },
    { field: 'provider_code', title: '服务商编码', width: 120 },
    { field: 'provider_name', title: '服务商名称', minWidth: 150 },
    { field: 'service_type', title: '服务类型', width: 120 },
    { field: 'payment_method', title: '付款方式', width: 100 },
    { field: 'settlement_cycle', title: '结算周期', width: 100 },
    { field: 'contact_name', title: '联系人', width: 100 },
    { field: 'contact_phone', title: '联系电话', width: 130 },
    { 
      field: 'is_active', 
      title: '状态', 
      width: 80,
      slots: { default: 'is_active_default' }
    },
    { 
      title: '操作', 
      width: 150, 
      fixed: 'right',
      slots: { default: 'action_default' }
    },
  ],
  data: [],
  pagerConfig: { enabled: true },
  toolbarConfig: {
    refresh: { code: 'query' },
    custom: true,
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

// 数据加载
async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getLogisticsProviders();
    gridApi.setGridOptions({ data: res });
  } catch (e) {
    console.error(e);
  } finally {
    gridApi.setLoading(false);
  }
}

onMounted(() => {
  loadData();
});

// 新建/编辑
const showModal = ref(false);
const editingId = ref<number | null>(null);

function handleCreate() {
  editingId.value = null;
  showModal.value = true;
}

function handleEdit(row: any) {
  editingId.value = row.id;
  showModal.value = true;
}

function handleModalClose() {
  showModal.value = false;
  loadData();
}
</script>

<template>
  <div class="p-4">
    <Grid>
      <!-- 工具栏 -->
      <template #toolbar_buttons>
        <a-button type="primary" @click="handleCreate">
          新建服务商
        </a-button>
      </template>
      
      <!-- 状态列 -->
      <template #is_active_default="{ row }">
        <a-tag :color="row.is_active ? 'green' : 'red'">
          {{ row.is_active ? '启用' : '停用' }}
        </a-tag>
      </template>
      
      <!-- 操作列 -->
      <template #action_default="{ row }">
        <a-space>
          <a-button type="link" size="small" @click="handleEdit(row)">
            编辑
          </a-button>
          <a-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
            <a-button type="link" danger size="small">删除</a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </Grid>
    
    <!-- 表单弹窗 -->
    <ProviderFormModal 
      v-if="showModal"
      :visible="showModal"
      :provider-id="editingId"
      @close="handleModalClose"
    />
  </div>
</template>
```

---

### 3.9 前端 - 路由配置

#### 📂 `frontend/apps/web-antd/src/router/routes/modules/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `logistics.ts` | 🔧 调整 | 增加物流服务商路由 |

**调整内容**：
```typescript
// 现有代码
import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/logistics',
    name: 'Logistics',
    component: () => import('#/layouts/index.vue'),
    meta: { title: '物流管理', icon: 'mdi:truck' },
    children: [
      // 现有：发货单管理
      {
        path: 'shipment',
        name: 'LogisticsShipment',
        component: () => import('#/views/logistics/shipment/index.vue'),
        meta: { title: '发货单管理' },
      },
      // 新增：物流服务商管理
      {
        path: 'provider',
        name: 'LogisticsProvider',
        component: () => import('#/views/logistics/provider/index.vue'),
        meta: { 
          title: '物流服务商管理',
          authority: 'logistics:provider:view'
        },
      },
    ],
  },
];

export default routes;
```

---

## 四、阶段2：物流服务明细关联（2-3天）

### 4.1 后端 - 数据库迁移

#### 📂 `backend/migrations/versions/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `[timestamp]_add_shipment_logistics_services.py` | 🆕 新建 | 创建发货单物流服务明细表 |

**迁移内容**：
```python
"""创建发货单物流服务明细表"""
def upgrade():
    op.create_table(
        'shipment_logistics_services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=False),
        sa.Column('logistics_provider_id', sa.Integer(), nullable=False),
        sa.Column('service_type', sa.String(50), nullable=False),
        sa.Column('service_description', sa.Text()),
        sa.Column('estimated_amount', sa.DECIMAL(18, 2)),
        sa.Column('actual_amount', sa.DECIMAL(18, 2)),
        sa.Column('currency', sa.String(10), default='CNY'),
        sa.Column('payment_method', sa.String(20)),
        sa.Column('service_voucher_id', sa.Integer()),  # 外键 → document_center
        sa.Column('payment_voucher_id', sa.Integer()),  # 外键 → document_center
        sa.Column('status', sa.String(20), default='pending'),  # pending/confirmed/reconciled/paid
        sa.Column('confirmed_at', sa.DateTime()),
        sa.Column('reconciled_at', sa.DateTime()),
        sa.Column('paid_at', sa.DateTime()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipment_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['logistics_provider_id'], ['logistics_providers.id']),
        sa.ForeignKeyConstraint(['service_voucher_id'], ['document_center.id']),
        sa.ForeignKeyConstraint(['payment_voucher_id'], ['document_center.id']),
    )
    
    # 索引
    op.create_index('idx_sls_shipment_id', 'shipment_logistics_services', ['shipment_id'])
    op.create_index('idx_sls_provider_id', 'shipment_logistics_services', ['logistics_provider_id'])
    op.create_index('idx_sls_status', 'shipment_logistics_services', ['status'])
```

---

### 4.2 后端 - Models

#### 📂 `backend/app/models/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `shipment_logistics_service.py` | 🆕 新建 | 发货单物流服务明细模型 |
| `shipment.py` | 🔧 调整 | 增加relationship |

**新建文件内容**（`shipment_logistics_service.py`）：
```python
"""
发货单物流服务明细模型 (ShipmentLogisticsService)
记录一个发货单对应的多个物流服务商及其费用

【重要】：
- 费用采用手工录入方式（物流服务商无API接口）
- estimated_amount: 预估费用（发货前由跟单人员根据报价录入）
- actual_amount: 实际费用（收到账单后由财务人员录入）
"""
from enum import Enum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

if TYPE_CHECKING:
    from app.models.logistics.shipment import ShipmentOrder
    from app.models.logistics.logistics_provider import LogisticsProvider
    from app.models.document.document_center import DocumentCenter

class ServiceStatus(str, Enum):
    """服务状态"""
    PENDING = 'pending'          # 待确认
    CONFIRMED = 'confirmed'      # 已确认
    RECONCILED = 'reconciled'    # 已对账
    PAID = 'paid'                # 已付款

class ShipmentLogisticsService(db.Model):
    """发货单物流服务明细表"""
    __tablename__ = "shipment_logistics_services"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipment_orders.id", ondelete="CASCADE"))
    logistics_provider_id: Mapped[int] = mapped_column(ForeignKey("logistics_providers.id"))
    
    # 服务信息
    service_type: Mapped[str] = mapped_column(String(50), comment='服务类型')
    service_description: Mapped[Optional[str]] = mapped_column(Text, comment='服务描述')
    
    # 费用信息
    estimated_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='预估费用')
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='实际费用')
    currency: Mapped[str] = mapped_column(String(10), default='CNY', comment='币种')
    payment_method: Mapped[Optional[str]] = mapped_column(String(20), comment='付款方式')
    
    # 凭证关联
    service_voucher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("document_center.id"), comment='服务凭证ID')
    payment_voucher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("document_center.id"), comment='付款凭证ID')
    
    # 状态与时间
    status: Mapped[str] = mapped_column(String(20), default=ServiceStatus.PENDING.value)
    confirmed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, comment='确认时间')
    reconciled_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, comment='对账时间')
    paid_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, comment='付款时间')
    
    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    
    # 审计字段
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, onupdate=func.now())
    
    # Relationships
    shipment: Mapped["ShipmentOrder"] = relationship("ShipmentOrder", back_populates="logistics_services")
    logistics_provider: Mapped["LogisticsProvider"] = relationship("LogisticsProvider")
    service_voucher: Mapped[Optional["DocumentCenter"]] = relationship(
        "DocumentCenter", 
        foreign_keys=[service_voucher_id]
    )
    payment_voucher: Mapped[Optional["DocumentCenter"]] = relationship(
        "DocumentCenter", 
        foreign_keys=[payment_voucher_id]
    )
```

**调整文件内容**（`shipment.py`）：
```python
# 在 ShipmentOrder 类中新增 relationship
class ShipmentOrder(db.Model):
    # ... 现有代码 ...
    
    # 新增：物流服务明细关系
    logistics_services: Mapped[List["ShipmentLogisticsService"]] = relationship(
        "ShipmentLogisticsService",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="ShipmentLogisticsService.id"
    )
```

---

### 4.3 后端 - Schemas

#### 📂 `backend/app/schemas/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `shipment_logistics_service.py` | 🆕 新建 | 物流服务明细Schema |

---

### 4.4 后端 - Services

#### 📂 `backend/app/services/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `shipment_logistics_service.py` | 🆕 新建 | 物流服务明细业务逻辑 |

**新建内容**：
```python
"""
发货单物流服务明细服务层
处理物流服务的添加、更新、确认、对账等业务逻辑
"""
from typing import List
from decimal import Decimal
from datetime import datetime
from app.models.logistics.shipment_logistics_service import ShipmentLogisticsService
from app.models.logistics.shipment import ShipmentOrder
from app.extensions import db
from app.errors import BusinessError

class ShipmentLogisticsServiceService:
    """物流服务明细业务逻辑类"""
    
    @staticmethod
    def add_service(shipment_id: int, data: dict):
        """为发货单添加物流服务"""
        # 验证发货单存在
        shipment = ShipmentOrder.query.get(shipment_id)
        if not shipment:
            raise BusinessError('发货单不存在', code=404)
        
        # 创建物流服务
        service = ShipmentLogisticsService(
            shipment_id=shipment_id,
            **data
        )
        db.session.add(service)
        db.session.commit()
        return service
    
    @staticmethod
    def get_services_by_shipment(shipment_id: int) -> List[ShipmentLogisticsService]:
        """获取发货单的所有物流服务"""
        return ShipmentLogisticsService.query.filter_by(shipment_id=shipment_id).all()
    
    @staticmethod
    def calculate_total_cost(shipment_id: int) -> Decimal:
        """计算发货单的物流总费用"""
        services = ShipmentLogisticsServiceService.get_services_by_shipment(shipment_id)
        total = sum(s.actual_amount or s.estimated_amount or 0 for s in services)
        return Decimal(total)
    
    @staticmethod
    def confirm_service(service_id: int):
        """确认物流服务"""
        service = ShipmentLogisticsService.query.get(service_id)
        if not service:
            raise BusinessError('物流服务不存在', code=404)
        
        service.status = 'confirmed'
        service.confirmed_at = datetime.now()
        db.session.commit()
        return service
    
    # ... 其他方法
```

---

### 4.5 后端 - API Routes

#### 📂 `backend/app/api/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `shipment_logistics_service_routes.py` | 🆕 新建 | 物流服务明细API路由 |

**新建内容**：
```python
"""发货单物流服务明细API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from app.security import auth
from app.schemas.logistics.shipment_logistics_service import (
    ShipmentLogisticsServiceSchema,
    ShipmentLogisticsServiceCreateSchema
)
from app.services.logistics.shipment_logistics_service import ShipmentLogisticsServiceService

shipment_logistics_bp = APIBlueprint(
    'shipment_logistics', 
    __name__, 
    url_prefix='/shipments/<int:shipment_id>/logistics-services',
    tag='发货单物流服务'
)

class ShipmentLogisticsServiceListAPI(MethodView):
    """发货单物流服务列表API"""
    decorators = [shipment_logistics_bp.auth_required(auth)]
    
    @shipment_logistics_bp.doc(summary='获取发货单的物流服务列表')
    @shipment_logistics_bp.output(ShipmentLogisticsServiceSchema(many=True))
    def get(self, shipment_id):
        """获取物流服务列表"""
        services = ShipmentLogisticsServiceService.get_services_by_shipment(shipment_id)
        return {'data': services}
    
    @shipment_logistics_bp.doc(summary='为发货单添加物流服务')
    @shipment_logistics_bp.input(ShipmentLogisticsServiceCreateSchema, arg_name='data')
    @shipment_logistics_bp.output(ShipmentLogisticsServiceSchema, status_code=201)
    def post(self, shipment_id, data):
        """添加物流服务"""
        service = ShipmentLogisticsServiceService.add_service(shipment_id, data)
        return {'data': service}

# 注册路由
shipment_logistics_bp.add_url_rule('', view_func=ShipmentLogisticsServiceListAPI.as_view('list'))
```

---

### 4.6 前端 - API封装

#### 📂 `frontend/apps/web-antd/src/api/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `shipment-logistics-service.ts` | 🆕 新建 | 物流服务明细API封装 |

**新建内容**：
```typescript
import { request } from '@vben/request';

export interface ShipmentLogisticsService {
  id: number;
  shipment_id: number;
  logistics_provider_id: number;
  logistics_provider_name: string;
  service_type: string;
  service_description?: string;
  estimated_amount?: number;
  actual_amount?: number;
  currency: string;
  payment_method?: string;
  status: string;
  service_voucher_id?: number;
  payment_voucher_id?: number;
  created_at: string;
}

/**
 * 获取发货单的物流服务列表
 */
export function getShipmentLogisticsServices(shipmentId: number) {
  return request<ShipmentLogisticsService[]>({
    url: `/api/v1/shipments/${shipmentId}/logistics-services`,
    method: 'GET',
  });
}

/**
 * 为发货单添加物流服务
 */
export function addShipmentLogisticsService(shipmentId: number, data: any) {
  return request<ShipmentLogisticsService>({
    url: `/api/v1/shipments/${shipmentId}/logistics-services`,
    method: 'POST',
    data,
  });
}

/**
 * 删除物流服务
 */
export function deleteShipmentLogisticsService(shipmentId: number, serviceId: number) {
  return request({
    url: `/api/v1/shipments/${shipmentId}/logistics-services/${serviceId}`,
    method: 'DELETE',
  });
}

/**
 * 更新物流服务
 */
export function updateShipmentLogisticsService(shipmentId: number, serviceId: number, data: any) {
  return request<ShipmentLogisticsService>({
    url: `/api/v1/shipments/${shipmentId}/logistics-services/${serviceId}`,
    method: 'PUT',
    data,
  });
}
```

---

### 4.7 前端 - 组件开发

#### 📂 `frontend/apps/web-antd/src/views/logistics/shipment/components/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `LogisticsServicesPanel.vue` | 🆕 新建 | 物流服务Tab面板 |
| `LogisticsServiceFormModal.vue` | 🆕 新建 | 添加物流服务弹窗 |
| `FinanceTab.vue` | 🔧 调整 | 调整为从物流服务明细汇总费用 |

**新建文件**（`LogisticsServicesPanel.vue`）：
```vue
<script setup lang="ts">
/**
 * 发货单详情 - 物流服务Tab
 * 展示物流服务明细列表，支持添加、编辑、删除、上传凭证
 */
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { 
  getShipmentLogisticsServices, 
  deleteShipmentLogisticsService 
} from '#/api/logistics/shipment-logistics-service';
import { onMounted, ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import LogisticsServiceFormModal from './LogisticsServiceFormModal.vue';

const props = defineProps<{
  shipmentId: number;
}>();

// Grid配置
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 60 },
    { field: 'logistics_provider_name', title: '物流服务商', minWidth: 150 },
    { field: 'service_type', title: '服务类型', width: 120 },
    { field: 'service_description', title: '服务描述', minWidth: 200 },
    { 
      field: 'estimated_amount', 
      title: '预估费用', 
      width: 110,
      slots: { default: 'amount_default' }
    },
    { 
      field: 'actual_amount', 
      title: '实际费用', 
      width: 110,
      slots: { default: 'amount_default' }
    },
    { field: 'payment_method', title: '付款方式', width: 100 },
    { 
      field: 'status', 
      title: '状态', 
      width: 90,
      slots: { default: 'status_default' }
    },
    { 
      title: '凭证', 
      width: 150,
      slots: { default: 'voucher_default' }
    },
    { 
      title: '操作', 
      width: 120, 
      fixed: 'right',
      slots: { default: 'action_default' }
    },
  ],
  data: [],
  toolbarConfig: {
    refresh: { code: 'query' },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ 
  gridOptions,
  gridEvents: {
    toolbarToolClick: (params) => {
      if (params.code === 'query') loadData();
    }
  }
});

// 加载数据
async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getShipmentLogisticsServices(props.shipmentId);
    gridApi.setGridOptions({ data: res });
  } catch (e: any) {
    message.error('加载物流服务失败');
  } finally {
    gridApi.setLoading(false);
  }
}

onMounted(() => {
  loadData();
});

// 新建/编辑
const showModal = ref(false);
const editingId = ref<number | null>(null);

function handleAdd() {
  editingId.value = null;
  showModal.value = true;
}

function handleEdit(row: any) {
  editingId.value = row.id;
  showModal.value = true;
}

function handleModalClose() {
  showModal.value = false;
  loadData();
}

// 计算总费用
const totalCost = computed(() => {
  const data = gridApi.getTableData().fullData;
  return data.reduce((sum, item) => {
    return sum + (item.actual_amount || item.estimated_amount || 0);
  }, 0);
});

// 辅助函数：状态颜色映射
function getStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    pending: 'default',
    confirmed: 'blue',
    reconciled: 'orange',
    paid: 'green',
  };
  return colorMap[status] || 'default';
}

// 辅助函数：状态文本映射
function getStatusText(status: string): string {
  const textMap: Record<string, string> = {
    pending: '待确认',
    confirmed: '已确认',
    reconciled: '已对账',
    paid: '已付款',
  };
  return textMap[status] || status;
}

// 辅助函数：查看凭证
function viewVoucher(voucherId: number) {
  // TODO: 实现凭证预览逻辑
  console.log('查看凭证:', voucherId);
}

// 辅助函数：删除物流服务
async function handleDelete(id: number) {
  try {
    await deleteShipmentLogisticsService(props.shipmentId, id);
    message.success('删除成功');
    loadData();
  } catch (e: any) {
    message.error('删除失败');
  }
}
</script>

<template>
  <div>
    <!-- 工具栏 -->
    <div class="mb-4 flex justify-between items-center">
      <a-button type="primary" @click="handleAdd">
        添加物流服务
      </a-button>
      <a-statistic 
        title="物流总费用" 
        :value="totalCost" 
        :precision="2" 
        prefix="¥"
        class="text-right"
      />
    </div>
    
    <!-- 表格 -->
    <Grid>
      <!-- 金额列 -->
      <template #amount_default="{ row, column }">
        <span v-if="row[column.field]">
          ¥{{ row[column.field].toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}
        </span>
        <span v-else class="text-gray-400">-</span>
      </template>
      
      <!-- 状态列 -->
      <template #status_default="{ row }">
        <a-tag :color="getStatusColor(row.status)">
          {{ getStatusText(row.status) }}
        </a-tag>
      </template>
      
      <!-- 凭证列 -->
      <template #voucher_default="{ row }">
        <a-space direction="vertical" size="small">
          <a-button 
            v-if="row.service_voucher_id" 
            type="link" 
            size="small"
            @click="viewVoucher(row.service_voucher_id)"
          >
            查看服务凭证
          </a-button>
          <a-button 
            v-if="row.payment_voucher_id" 
            type="link" 
            size="small"
            @click="viewVoucher(row.payment_voucher_id)"
          >
            查看付款凭证
          </a-button>
        </a-space>
      </template>
      
      <!-- 操作列 -->
      <template #action_default="{ row }">
        <a-space>
          <a-button type="link" size="small" @click="handleEdit(row)">
            编辑
          </a-button>
          <a-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
            <a-button type="link" danger size="small">删除</a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </Grid>
    
    <!-- 表单弹窗 -->
    <LogisticsServiceFormModal 
      v-if="showModal"
      :visible="showModal"
      :shipment-id="shipmentId"
      :service-id="editingId"
      @close="handleModalClose"
    />
  </div>
</template>
```

**调整文件**（`FinanceTab.vue`）：
```vue
<script setup lang="ts">
/**
 * 发货单详情 - 财务Tab
 * 从物流服务明细汇总费用，不再直接使用shipment表的冗余字段
 */
import { onMounted, ref, computed } from 'vue';
import { Alert, Card, Statistic } from 'ant-design-vue';
import { getShipmentLogisticsServices } from '#/api/logistics/shipment-logistics-service';

const props = defineProps<{
  shipmentId: number;
}>();

const logisticsServices = ref<any[]>([]);

async function loadServices() {
  logisticsServices.value = await getShipmentLogisticsServices(props.shipmentId);
}

// 计算物流总费用
const totalLogisticsCost = computed(() => {
  return logisticsServices.value.reduce((sum, item) => {
    return sum + (item.actual_amount || item.estimated_amount || 0);
  }, 0);
});

onMounted(() => {
  loadServices();
});

// 定义表格列
const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '物流服务商', dataIndex: 'logistics_provider_name', key: 'provider', minWidth: 150 },
  { title: '服务类型', dataIndex: 'service_type', key: 'type', width: 120 },
  { title: '预估费用', dataIndex: 'estimated_amount', key: 'estimated', width: 110 },
  { title: '实际费用', dataIndex: 'actual_amount', key: 'actual', width: 110 },
];
</script>

<template>
  <div>
    <Alert type="info" show-icon class="mb-4">
      <template #message>
        <span class="font-semibold">关于物流成本</span>
      </template>
      <template #description>
        <p class="text-sm">
          物流成本从"物流服务"Tab中的明细汇总计算,支持多个物流服务商的费用分项管理。
        </p>
      </template>
    </Alert>
    
    <!-- 物流成本汇总 -->
    <Card title="物流成本汇总" class="mb-4">
      <Statistic
        title="物流总成本"
        :value="totalLogisticsCost"
        :precision="2"
        prefix="¥"
        :value-style="{ color: '#cf1322', fontSize: '24px' }"
      />
    </Card>
    
    <!-- 物流服务明细 -->
    <Card title="物流服务明细">
      <a-table 
        :columns="columns" 
        :data-source="logisticsServices"
        :pagination="false"
        size="small"
      />
    </Card>
  </div>
</template>
```

---

### 4.8 前端 - 详情页Tab集成

#### 📂 `frontend/apps/web-antd/src/views/logistics/shipment/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `detail.vue` | 🔧 调整 | 增加物流服务Tab |

**调整内容**：
```vue
<script setup lang="ts">
// 导入新组件
import LogisticsServicesPanel from './components/LogisticsServicesPanel.vue';

// ... 现有代码 ...
</script>

<template>
  <div>
    <!-- ... 现有代码 ... -->
    
    <Tabs v-model:activeKey="activeTab">
      <TabPane key="overview" tab="概览">
        <OverviewTab :shipment="shipment" />
      </TabPane>
      <TabPane key="goods" tab="商品明细">
        <GoodsTab :shipment="shipment" />
      </TabPane>
      
      <!-- 新增：物流服务Tab -->
      <TabPane key="logistics-services" tab="物流服务">
        <LogisticsServicesPanel :shipment-id="shipmentId" />
      </TabPane>
      
      <TabPane key="purchase" tab="采购明细">
        <PurchaseTab :shipment-id="shipmentId" />
      </TabPane>
      <TabPane key="logistics" tab="物流信息">
        <LogisticsTab :shipment="shipment" />
      </TabPane>
      <TabPane key="finance" tab="财务信息">
        <FinanceTab :shipment-id="shipmentId" />
      </TabPane>
      <TabPane key="documents" tab="凭证管理">
        <DocumentsTab :shipment-id="shipmentId" />
      </TabPane>
      <TabPane key="history" tab="操作历史">
        <HistoryTab :shipment-id="shipmentId" />
      </TabPane>
    </Tabs>
  </div>
</template>
```

---

## 五、阶段3：凭证管理中心（3-4天）

### 5.1 后端 - Services扩展

#### 📂 `backend/app/services/document/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `document_service.py` | 🔧 完善 | 实现完整的上传/查询/归档逻辑 |
| `archive_service.py` | 🆕 新建 | 自动归档服务 |

**完善内容**（`document_service.py`）：
```python
"""
凭证管理服务层
处理凭证上传、查询、审核、归档等业务逻辑
"""
from typing import List, Optional
from datetime import datetime
import os
from app.models.document.document_center import DocumentCenter, BusinessType
from app.extensions import db
from app.errors import BusinessError

class DocumentService:
    """凭证管理业务逻辑类"""
    
    @staticmethod
    def upload_document(business_type: str, business_id: int, file, metadata: dict, uploaded_by: int):
        """
        上传凭证
        
        Args:
            business_type: 业务类型(logistics/purchase/customs/payment)
            business_id: 业务单据ID
            file: 文件对象
            metadata: 元数据(document_type, document_category等)
            uploaded_by: 上传人ID
        """
        # 验证文件
        if not file:
            raise BusinessError('文件不能为空', code=400)
        
        # 生成文件路径（实际项目中应保存到OSS/NAS）
        file_name = file.filename
        file_path = f"uploads/{business_type}/{business_id}/{file_name}"
        
        # 保存文件（示例）
        # file.save(file_path)
        
        # 创建凭证记录
        document = DocumentCenter(
            business_type=business_type,
            business_id=business_id,
            document_type=metadata.get('document_type'),
            document_category=metadata.get('document_category'),
            file_name=file_name,
            file_path=file_path,
            file_size=len(file.read()),
            file_type=os.path.splitext(file_name)[1],
            uploaded_by_id=uploaded_by,
            uploaded_at=datetime.now()
        )
        
        db.session.add(document)
        db.session.commit()
        return document
    
    @staticmethod
    def get_documents_by_business(business_type: str, business_id: int) -> List[DocumentCenter]:
        """按业务单据查询凭证"""
        return DocumentCenter.query.filter_by(
            business_type=business_type,
            business_id=business_id
        ).all()
    
    @staticmethod
    def get_documents_by_shipment(shipment_id: int) -> List[DocumentCenter]:
        """获取发货单的所有凭证"""
        return DocumentService.get_documents_by_business('logistics', shipment_id)
    
    @staticmethod
    def approve_document(document_id: int, approved_by: int, notes: Optional[str] = None):
        """审核凭证"""
        document = DocumentCenter.query.get(document_id)
        if not document:
            raise BusinessError('凭证不存在', code=404)
        
        document.audit_status = 'approved'
        document.audited_by_id = approved_by
        document.audited_at = datetime.now()
        document.audit_notes = notes
        
        db.session.commit()
        return document
    
    # ... 其他方法
```

**新建内容**（`archive_service.py`）：
```python
"""
自动归档服务
当报关单审核通过后，自动打包所有相关凭证进行归档
"""
from typing import List
from datetime import datetime
import os
import zipfile
from app.models.document.document_center import DocumentCenter
from app.models.customs.declaration import CustomsDeclaration
from app.extensions import db
from app.errors import BusinessError

class ArchiveService:
    """归档服务类"""
    
    @staticmethod
    def archive_by_customs_declaration(declaration_id: int) -> str:
        """
        按报关单归档
        
        Returns:
            归档文件路径
        """
        from app.services.document.document_service import DocumentService
        
        declaration = CustomsDeclaration.query.get(declaration_id)
        if not declaration:
            raise BusinessError('报关单不存在', code=404)
        
        # 收集所有相关凭证
        documents = []
        
        # 1. 报关单凭证
        customs_docs = DocumentService.get_documents_by_business('customs', declaration_id)
        documents.extend(customs_docs)
        
        # 2. 发货单凭证
        if declaration.shipment_id:
            shipment_docs = DocumentService.get_documents_by_business('logistics', declaration.shipment_id)
            documents.extend(shipment_docs)
        
        # 3. 打包成ZIP
        archive_path = f"archives/customs_{declaration.declaration_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        with zipfile.ZipFile(archive_path, 'w') as zipf:
            for doc in documents:
                zipf.write(doc.file_path, arcname=doc.file_name)
        
        # 4. 更新归档状态
        for doc in documents:
            doc.archived = True
            doc.archive_path = archive_path
            doc.archived_at = datetime.now()
        
        db.session.commit()
        
        return archive_path
    
    @staticmethod
    def archive_by_shipment(shipment_id: int) -> str:
        """按发货单归档"""
        # 类似逻辑
        pass
    
    @staticmethod
    def archive_by_supplier(supplier_id: int, start_date, end_date) -> str:
        """按供应商归档"""
        # 类似逻辑
        pass
    
    @staticmethod
    def archive_by_month(year: int, month: int) -> str:
        """按月度归档"""
        # 类似逻辑
        pass
```

---

### 5.2 后端 - API Routes扩展

#### 📂 `backend/app/api/document/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `document_routes.py` | 🔧 完善 | 实现完整的API接口 |

**完善内容**：
```python
"""凭证管理API路由"""
from apiflask import APIBlueprint, FileSchema
from apiflask.views import MethodView
from flask import request
from flask_jwt_extended import get_jwt_identity
from app.security import auth
from app.services.document.document_service import DocumentService
from app.services.document.archive_service import ArchiveService

document_bp = APIBlueprint('documents', __name__, url_prefix='/documents', tag='凭证管理')

class DocumentUploadAPI(MethodView):
    """凭证上传API"""
    decorators = [document_bp.auth_required(auth)]
    
    @document_bp.doc(summary='上传凭证')
    @document_bp.input(FileSchema, location='files', arg_name='files')
    def post(self):
        """上传凭证"""
        user_id = get_jwt_identity()
        
        # 获取参数
        business_type = request.form.get('business_type')
        business_id = request.form.get('business_id')
        document_type = request.form.get('document_type')
        document_category = request.form.get('document_category')
        
        # 获取文件
        file = request.files.get('file')
        
        # 上传
        document = DocumentService.upload_document(
            business_type=business_type,
            business_id=business_id,
            file=file,
            metadata={
                'document_type': document_type,
                'document_category': document_category
            },
            uploaded_by=user_id
        )
        
        return {'data': document}

class DocumentListAPI(MethodView):
    """凭证列表API"""
    decorators = [document_bp.auth_required(auth)]
    
    @document_bp.doc(summary='查询凭证列表')
    def get(self):
        """查询凭证"""
        business_type = request.args.get('business_type')
        business_id = request.args.get('business_id')
        
        if business_type and business_id:
            documents = DocumentService.get_documents_by_business(business_type, int(business_id))
        else:
            # 查询所有
            documents = DocumentCenter.query.all()
        
        return {'data': documents}

class ArchiveAPI(MethodView):
    """归档API"""
    decorators = [document_bp.auth_required(auth)]
    
    @document_bp.doc(summary='按报关单归档')
    def post(self):
        """触发归档"""
        archive_type = request.json.get('archive_type')  # shipment/customs/supplier/month
        archive_id = request.json.get('archive_id')
        
        if archive_type == 'customs':
            archive_path = ArchiveService.archive_by_customs_declaration(archive_id)
        elif archive_type == 'shipment':
            archive_path = ArchiveService.archive_by_shipment(archive_id)
        # ... 其他类型
        
        return {'data': {'archive_path': archive_path}}

# 注册路由
document_bp.add_url_rule('/upload', view_func=DocumentUploadAPI.as_view('upload'))
document_bp.add_url_rule('', view_func=DocumentListAPI.as_view('list'))
document_bp.add_url_rule('/archive', view_func=ArchiveAPI.as_view('archive'))
```

---

### 5.3 前端 - 通用组件开发

#### 📂 `frontend/apps/web-antd/src/components/document/`（新建目录）

| 文件 | 类型 | 说明 |
|------|------|------|
| `DocumentUploader.vue` | 🆕 新建 | 凭证上传组件（支持拖拽、多文件） |
| `DocumentList.vue` | 🆕 新建 | 凭证列表展示组件 |
| `DocumentPreview.vue` | 🆕 新建 | 凭证预览组件（PDF/图片/Excel） |

**新建内容**（`DocumentUploader.vue`）：
```vue
<script setup lang="ts">
/**
 * 通用凭证上传组件
 * 支持拖拽、多文件、预览、删除
 */
import { Upload, message } from 'ant-design-vue';
import { InboxOutlined } from '@ant-design/icons-vue';
import { ref } from 'vue';
import { uploadDocument } from '#/api/document/document';

const props = defineProps<{
  businessType: string;  // logistics/purchase/customs/payment
  businessId: number;
  documentType: string;
  documentCategory: string;
}>();

const emit = defineEmits<{
  (e: 'success'): void;
}>();

const fileList = ref<any[]>([]);
const uploading = ref(false);

const uploadProps = {
  name: 'file',
  multiple: true,
  accept: '.pdf,.jpg,.jpeg,.png,.xlsx,.xls',
  customRequest: async (options: any) => {
    try {
      uploading.value = true;
      
      const formData = new FormData();
      formData.append('file', options.file);
      formData.append('business_type', props.businessType);
      formData.append('business_id', String(props.businessId));
      formData.append('document_type', props.documentType);
      formData.append('document_category', props.documentCategory);
      
      await uploadDocument(formData);
      
      message.success(`${options.file.name} 上传成功`);
      options.onSuccess();
      emit('success');
    } catch (error: any) {
      message.error(`${options.file.name} 上传失败: ${error.message}`);
      options.onError(error);
    } finally {
      uploading.value = false;
    }
  },
  onChange(info: any) {
    fileList.value = info.fileList;
  },
};
</script>

<template>
  <div>
    <Upload.Dragger v-bind="uploadProps" :file-list="fileList">
      <p class="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p class="ant-upload-hint">
        支持 PDF、图片、Excel 格式，可一次上传多个文件
      </p>
    </Upload.Dragger>
  </div>
</template>
```

---

### 5.4 前端 - 集成到业务页面

#### 📂 `frontend/apps/web-antd/src/views/logistics/shipment/components/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `DocumentsTab.vue` | 🔧 调整 | 使用通用凭证组件 |
| `LogisticsServiceFormModal.vue` | 🔧 调整 | 集成凭证上传 |

**调整内容**（`DocumentsTab.vue`）：
```vue
<script setup lang="ts">
/**
 * 发货单详情 - 凭证管理Tab
 * 使用通用凭证组件
 */
import { ref, onMounted } from 'vue';
import { Card } from 'ant-design-vue';
import DocumentUploader from '#/components/document/DocumentUploader.vue';
import DocumentList from '#/components/document/DocumentList.vue';
import { getDocumentsByBusiness } from '#/api/document/document';

const props = defineProps<{
  shipmentId: number;
}>();

const documents = ref<any[]>([]);

async function loadDocuments() {
  documents.value = await getDocumentsByBusiness('logistics', props.shipmentId);
}

onMounted(() => {
  loadDocuments();
});

function handleUploadSuccess() {
  loadDocuments();
}
</script>

<template>
  <div>
    <!-- 上传区 -->
    <Card title="上传凭证" class="mb-4">
      <DocumentUploader 
        business-type="logistics"
        :business-id="shipmentId"
        document-type="logistics_voucher"
        document-category="service_voucher"
        @success="handleUploadSuccess"
      />
    </Card>
    
    <!-- 凭证列表 -->
    <Card title="已上传凭证">
      <DocumentList :documents="documents" @refresh="loadDocuments" />
    </Card>
  </div>
</template>
```

---

## 六、阶段4：物流对账与付款（3-4天）

### 6.1 后端 - 数据库迁移

#### 📂 `backend/migrations/versions/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `[timestamp]_add_logistics_statement_and_payment.py` | 🆕 新建 | 创建物流对账单和物流付款单表 |

**迁移内容**：
```python
"""创建物流对账单和物流付款单表"""
def upgrade():
    # 1. 创建物流对账单表
    op.create_table(
        'logistics_statements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('statement_no', sa.String(50), unique=True, nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=False),
        sa.Column('logistics_provider_id', sa.Integer(), nullable=False),
        sa.Column('statement_date', sa.Date()),
        sa.Column('total_amount', sa.DECIMAL(18, 2)),
        sa.Column('currency', sa.String(10), default='CNY'),
        sa.Column('payment_method', sa.String(20)),
        sa.Column('status', sa.String(20), default='draft'),  # draft/confirmed/paid
        sa.Column('confirmed_by_id', sa.Integer()),
        sa.Column('confirmed_at', sa.DateTime()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipment_orders.id']),
        sa.ForeignKeyConstraint(['logistics_provider_id'], ['logistics_providers.id']),
        sa.ForeignKeyConstraint(['confirmed_by_id'], ['users.id']),
    )
    
    # 2. 创建物流付款单表
    op.create_table(
        'logistics_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_no', sa.String(50), unique=True),
        sa.Column('statement_id', sa.Integer(), nullable=False),
        sa.Column('payment_date', sa.Date()),
        sa.Column('payment_amount', sa.DECIMAL(18, 2)),
        sa.Column('currency', sa.String(10)),
        sa.Column('payment_pool_id', sa.Integer()),  # 外键 → fin_payment_pool
        sa.Column('status', sa.String(20), default='pending'),  # pending/approved/paid
        sa.Column('approved_by_id', sa.Integer()),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('paid_at', sa.DateTime()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['statement_id'], ['logistics_statements.id']),
        sa.ForeignKeyConstraint(['payment_pool_id'], ['fin_payment_pool.id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id']),
    )
    
    # 索引
    op.create_index('idx_ls_shipment_id', 'logistics_statements', ['shipment_id'])
    op.create_index('idx_ls_provider_id', 'logistics_statements', ['logistics_provider_id'])
    op.create_index('idx_lp_statement_id', 'logistics_payments', ['statement_id'])
```

---

### 6.2 后端 - Models

#### 📂 `backend/app/models/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `logistics_statement.py` | 🆕 新建 | 物流对账单模型 |
| `logistics_payment.py` | 🆕 新建 | 物流付款单模型 |

---

### 6.3 后端 - Services

#### 📂 `backend/app/services/logistics/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `logistics_statement_service.py` | 🆕 新建 | 物流对账单业务逻辑 |
| `logistics_payment_service.py` | 🆕 新建 | 物流付款单业务逻辑 |

**新建内容**（`logistics_statement_service.py`）：
```python
"""
物流对账单服务层
处理物流对账单的创建、确认、生成付款单等业务逻辑

【重要说明】：
- 物流服务商无API接口，无法自动对账
- 对账单由财务人员根据服务商提供的纸质/电子账单手工核对后创建
- 系统提供从物流服务明细生成对账单草稿的功能，但金额需人工确认
"""
from datetime import datetime
from app.models.logistics.logistics_statement import LogisticsStatement
from app.models.logistics.shipment_logistics_service import ShipmentLogisticsService
from app.extensions import db
from app.errors import BusinessError

class LogisticsStatementService:
    """物流对账单业务逻辑类"""
    
    @staticmethod
    def generate_statement_from_services(shipment_id: int, provider_id: int, data: dict):
        """
        从物流服务明细生成对账单草稿（需人工确认金额）
        
        Args:
            shipment_id: 发货单ID
            provider_id: 物流服务商ID
            data: 对账单数据
        
        注意：
        - 生成的对账单为草稿状态，金额从actual_amount取值
        - 财务人员需核对服务商账单后，手工确认或调整金额
        """
        # 获取该服务商的所有物流服务
        services = ShipmentLogisticsService.query.filter_by(
            shipment_id=shipment_id,
            logistics_provider_id=provider_id,
            status='confirmed'  # 只对账已确认的服务
        ).all()
        
        if not services:
            raise BusinessError('没有可对账的物流服务', code=400)
        
        # 计算总金额
        total_amount = sum(s.actual_amount or s.estimated_amount or 0 for s in services)
        
        # 生成对账单号
        statement_no = f"LS{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 创建对账单
        statement = LogisticsStatement(
            statement_no=statement_no,
            shipment_id=shipment_id,
            logistics_provider_id=provider_id,
            statement_date=datetime.now().date(),
            total_amount=total_amount,
            currency=data.get('currency', 'CNY'),
            payment_method=data.get('payment_method'),
            status='draft'
        )
        
        db.session.add(statement)
        db.session.commit()
        
        # 更新物流服务状态
        for service in services:
            service.status = 'reconciled'
            service.reconciled_at = datetime.now()
        
        db.session.commit()
        
        return statement
    
    @staticmethod
    def confirm_statement(statement_id: int, confirmed_by: int):
        """确认对账单，自动生成付款单"""
        statement = LogisticsStatement.query.get(statement_id)
        if not statement:
            raise BusinessError('对账单不存在', code=404)
        
        if statement.status != 'draft':
            raise BusinessError('只能确认草稿状态的对账单', code=400)
        
        # 确认对账单
        statement.status = 'confirmed'
        statement.confirmed_by_id = confirmed_by
        statement.confirmed_at = datetime.now()
        
        db.session.commit()
        
        # 自动生成付款单
        from app.services.logistics.logistics_payment_service import LogisticsPaymentService
        payment = LogisticsPaymentService.create_payment_from_statement(statement_id)
        
        return statement, payment
```

---

## 七、阶段5：付款池扩展（2天）

### 7.1 后端 - 数据库迁移

#### 📂 `backend/migrations/versions/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `[timestamp]_extend_payment_pool_for_logistics.py` | 🆕 新建 | 扩展付款池支持物流费用 |

**迁移内容**：
```python
"""扩展付款池支持物流费用"""
def upgrade():
    # 1. 增加字段
    op.add_column('fin_payment_pool', 
        sa.Column('payment_type', sa.String(20), default='purchase', comment='付款类型: purchase/logistics/other')
    )
    op.add_column('fin_payment_pool',
        sa.Column('related_statement_type', sa.String(30), comment='关联对账单类型: purchase_soa/logistics_statement')
    )
    op.add_column('fin_payment_pool',
        sa.Column('related_statement_id', sa.Integer(), comment='关联对账单ID')
    )
    
    # 2. 更新现有数据（将现有记录标记为purchase类型）
    op.execute("UPDATE fin_payment_pool SET payment_type = 'purchase' WHERE payment_type IS NULL")
    
    # 3. 创建索引
    op.create_index('idx_fp_payment_type', 'fin_payment_pool', ['payment_type'])
```

---

### 7.2 后端 - Models扩展

#### 📂 `backend/app/models/serc/finance.py`

| 文件 | 类型 | 说明 |
|------|------|------|
| `finance.py` | 🔧 调整 | 扩展FinPaymentPool模型 |

**调整内容**：
```python
class FinPaymentPool(db.Model):
    """L3: 资金池/付款计划 (Payment Schedule)"""
    __tablename__ = "fin_payment_pool"
    
    # ... 现有字段 ...
    
    # 新增字段
    payment_type: Mapped[str] = mapped_column(
        String(20), 
        default='purchase', 
        comment='付款类型: purchase/logistics/other'
    )
    related_statement_type: Mapped[Optional[str]] = mapped_column(
        String(30), 
        comment='关联对账单类型: purchase_soa/logistics_statement'
    )
    related_statement_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        comment='关联对账单ID'
    )
    
    # ... 其余代码 ...
```

---

### 7.3 后端 - Services扩展

#### 📂 `backend/app/services/serc/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `payment_pool_service.py` | 🔧 调整 | 扩展支持物流费用 |

**调整内容**：
```python
class PaymentPoolService:
    """付款池业务逻辑类"""
    
    @staticmethod
    def add_to_pool(payment_type: str, statement_id: int, amount: Decimal, **kwargs):
        """
        加入付款池（统一入口）
        
        Args:
            payment_type: 'purchase' | 'logistics' | 'other'
            statement_id: 对账单ID
            amount: 付款金额
        """
        # 确定关联对账单类型
        if payment_type == 'purchase':
            related_type = 'purchase_soa'
        elif payment_type == 'logistics':
            related_type = 'logistics_statement'
        else:
            related_type = 'other'
        
        # 创建付款池记录
        pool_item = FinPaymentPool(
            payment_type=payment_type,
            related_statement_type=related_type,
            related_statement_id=statement_id,
            amount=amount,
            currency=kwargs.get('currency', 'CNY'),
            due_date=kwargs.get('due_date'),
            priority=kwargs.get('priority', 0),
            status='pending_approval'
        )
        
        db.session.add(pool_item)
        db.session.commit()
        return pool_item
    
    @staticmethod
    def get_pool_items(payment_type: Optional[str] = None):
        """获取付款池列表（支持按类型筛选）"""
        query = FinPaymentPool.query
        
        if payment_type:
            query = query.filter_by(payment_type=payment_type)
        
        return query.order_by(FinPaymentPool.priority.desc(), FinPaymentPool.due_date).all()
```

---

### 7.4 前端 - 页面调整

#### 📂 `frontend/apps/web-antd/src/views/serc/finance/`

| 文件 | 类型 | 说明 |
|------|------|------|
| `pool.vue` | 🔧 调整 | 增加付款类型筛选 |

**调整内容**：
```vue
<script setup lang="ts">
/**
 * 注意：以下是在现有 pool.vue 代码基础上的增量调整
 * 现有代码包含：
 * - import { ref } from 'vue';
 * - import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
 * - import { getPaymentPoolItems } from '#/api/serc/finance';
 * - 现有的 Grid 和 gridApi 初始化
 */

// 增加付款类型筛选
const paymentType = ref<string>('all');  // all/purchase/logistics

const gridOptions: VxeGridProps = {
  columns: [
    // ... 现有列 ...
    { 
      field: 'payment_type', 
      title: '付款类型', 
      width: 100,
      slots: { default: 'payment_type_default' }
    },
    // ...
  ],
  // ...
};

// 加载数据时传入筛选参数
async function loadData() {
  const params: any = {};
  if (paymentType.value !== 'all') {
    params.payment_type = paymentType.value;
  }
  
  const res = await getPaymentPoolItems(params);
  gridApi.setGridOptions({ data: res });
}

// 辅助函数：付款类型颜色映射
function getPaymentTypeColor(type: string): string {
  const colorMap: Record<string, string> = {
    purchase: 'blue',
    logistics: 'green',
    other: 'default',
  };
  return colorMap[type] || 'default';
}

// 辅助函数：付款类型文本映射
function getPaymentTypeText(type: string): string {
  const textMap: Record<string, string> = {
    purchase: '商品采购',
    logistics: '物流费用',
    other: '其他',
  };
  return textMap[type] || type;
}
</script>

<template>
  <div class="p-4">
    <!-- 筛选器 -->
    <div class="mb-4">
      <a-radio-group v-model:value="paymentType" @change="loadData">
        <a-radio-button value="all">全部</a-radio-button>
        <a-radio-button value="purchase">商品采购</a-radio-button>
        <a-radio-button value="logistics">物流费用</a-radio-button>
      </a-radio-group>
    </div>
    
    <Grid>
      <!-- 付款类型列 -->
      <template #payment_type_default="{ row }">
        <a-tag :color="getPaymentTypeColor(row.payment_type)">
          {{ getPaymentTypeText(row.payment_type) }}
        </a-tag>
      </template>
    </Grid>
  </div>
</template>
```

---

## 八、阶段6：集成测试与优化（2-3天）

### 8.1 后端 - 单元测试

#### 📂 `backend/tests/`

| 目录/文件 | 类型 | 说明 |
|----------|------|------|
| `test_logistics_provider.py` | 🆕 新建 | 物流服务商测试 |
| `test_logistics_statement.py` | 🆕 新建 | 物流对账单测试 |
| `test_document_service.py` | 🆕 新建 | 凭证管理测试 |
| `test_payment_pool_extension.py` | 🆕 新建 | 付款池扩展测试 |
| `integration/test_logistics_flow.py` | 🆕 新建 | 物流费用完整流程集成测试 |

**示例**（`test_logistics_provider.py`）：
```python
"""物流服务商单元测试"""
import pytest
from app.models.logistics.logistics_provider import LogisticsProvider
from app.services.logistics.logistics_provider_service import LogisticsProviderService

def test_create_logistics_provider(app, db):
    """测试创建物流服务商"""
    data = {
        'provider_name': '顺丰速运',
        'provider_code': 'SF001',
        'service_type': 'domestic_trucking',
        'payment_method': 'postpaid',
        'settlement_cycle': 'monthly'
    }
    
    provider = LogisticsProviderService.create_provider(data, created_by=1)
    
    assert provider.id is not None
    assert provider.provider_name == '顺丰速运'
    assert provider.provider_code == 'SF001'

def test_create_duplicate_provider_code(app, db):
    """测试创建重复编码的服务商"""
    # ... 测试逻辑
```

---

### 8.2 性能优化清单

| 优化项 | 位置 | 说明 |
|--------|------|------|
| 数据库索引检查 | 所有新建表 | 确保关键字段有索引 |
| N+1查询优化 | Services层 | 使用selectinload/joinedload |
| API响应时间监控 | 全局中间件 | 记录慢接口(>200ms) |
| 前端虚拟滚动 | 大列表组件 | 使用vxe-table的虚拟滚动 |
| 图片懒加载 | 凭证预览组件 | 使用IntersectionObserver |

---

## 九、废弃代码迁移计划

### 9.1 逐步废弃的文件

| 文件 | 废弃原因 | 迁移方案 |
|------|---------|----------|
| `backend/app/models/customs/attachment.py` | 替换为通用凭证管理 | 保留向后兼容，新业务使用document_center |
| `frontend/apps/web-antd/src/views/customs/declaration/components/DeclarationFilePanel.vue` | 替换为通用凭证组件 | 逐步迁移到DocumentUploader组件 |

---

## 十、总结

### 10.1 代码调整统计

| 类型 | 后端文件数 | 前端文件数 | 总计 |
|------|-----------|-----------|------|
| 🆕 新建 | 35+ | 20+ | 55+ |
| 🔧 调整 | 8+ | 10+ | 18+ |
| 🗑️ 废弃 | 2 | 2 | 4 |
| **总计** | **45+** | **32+** | **77+** |

### 10.2 关键调整点

1. **数据模型层**：新增7个表，扩展2个表
2. **业务逻辑层**：新增10+个Service类
3. **API接口层**：新增6个Blueprint，20+个API端点
4. **前端组件层**：新增3个通用组件，10+个业务组件
5. **集成点**：发货单详情页、付款池页面、凭证管理页面

### 10.3 业务流程约束（重要）

⚠️ **手工录入流程**：

1. **物流服务添加阶段**（跟单组）
   - 在发货单详情页"物流服务"Tab手工添加服务商
   - 手工填写服务类型、预估费用
   - 上传服务凭证（运单、提单、清关单等）

2. **费用确认阶段**（财务组）
   - 收到服务商账单后，手工录入实际费用
   - 上传付款凭证
   - 核对无误后，将服务状态标记为"已确认"

3. **对账单生成阶段**（财务组）
   - 系统从已确认的物流服务生成对账单草稿
   - 财务人员手工核对金额，确认对账单
   - 生成付款单，进入付款池

4. **无自动对账**
   - 不涉及API自动拉取费用
   - 不涉及自动对账逻辑
   - 所有金额依赖人工录入和确认

### 10.4 暂缓功能列表

以下功能**暂不实施**，待物流服务商提供API后再扩展：

| 功能 | 原因 | 未来扩展条件 |
|------|------|------------|
| ⏸️ 自动对接物流服务商API | 服务商无API | 服务商提供标准API |
| ⏸️ 自动获取费用 | 无数据源 | API提供费用查询接口 |
| ⏸️ 自动对账 | 需要API支持 | API提供账单数据 |
| ⏸️ 费用自动校验 | 无标准数据 | 建立费用基准库 |

### 10.5 下一步行动

1. ✅ **确认本清单** - 评估工作量和优先级
2. 📝 **启动阶段0** - 撰写3份详细设计文档
3. 🛠️ **启动阶段1** - 开始数据库迁移和基础模型开发
4. 🔄 **持续迭代** - 按6个阶段逐步推进

---

**文档状态**: ✅ 待确认  
**确认人**: [待填写]  
**确认日期**: [待填写]
