# 领星API使用指南

## 快速开始

### 1. 配置领星API密钥

在项目根目录的 `.env` 文件中添加以下配置（如果没有此文件，请参考 `backend/.env.lingxing.example`）：

```bash
# 领星ERP API配置
LINGXING_API_BASE_URL=https://api.lingxing.com
LINGXING_APP_KEY=你的app_key
LINGXING_APP_SECRET=你的app_secret
LINGXING_TIMEOUT=30
LINGXING_MAX_RETRIES=3
```

> **如何获取密钥？**
> 1. 登录领星ERP后台: https://erp.lingxing.com
> 2. 进入 **开发者中心** > **API管理**
> 3. 创建应用并获取 `app_key` 和 `app_secret`

### 2. 初始化权限

在项目根目录执行以下命令初始化领星相关权限：

```bash
docker compose exec backend flask lingxing init-permissions
```

输出示例：
```
创建权限: lingxing:shipment:view
创建权限: lingxing:stock:view
创建权限: lingxing:health:check

权限初始化完成!
- 新增: 3 个
- 更新: 0 个
- 总计: 3 个
```

### 3. 分配权限

在系统管理后台为相应角色分配以下权限：

- `lingxing:shipment:view` - 查看发货单
- `lingxing:stock:view` - 查看备货单
- `lingxing:health:check` - 健康检查

### 4. 重启后端服务

```bash
docker compose restart backend
```

---

## API接口说明

### 3.1 查询发货单详情

**接口地址**: `GET /api/v1/lingxing/shipments/detail`

**请求参数** (Query String):

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| shipment_id | string | 是 | 发货单ID | FBA12345678 |
| page | integer | 否 | 页码，默认1 | 1 |
| page_size | integer | 否 | 每页记录数，默认20 | 20 |

**请求示例**:

```bash
curl -X GET "http://localhost:5000/api/v1/lingxing/shipments/detail?shipment_id=FBA12345678&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "shipment_id": "FBA12345678",
    "shipment_name": "测试发货计划-202512",
    "destination_fulfillment_center_id": "PHX3",
    "shipment_status": "SHIPPED",
    "ship_from_address": {
      "name": "深圳仓库",
      "address_line1": "某某区某某路123号",
      "city": "深圳",
      "state_or_province": "广东省",
      "country_code": "CN",
      "postal_code": "518000"
    },
    "items": [
      {
        "sku": "TEST-SKU-001",
        "fnsku": "X001234567",
        "quantity_shipped": 100,
        "quantity_received": 95,
        "quantity_in_case": 10
      }
    ],
    "total_units": 100,
    "created_date": "2025-12-01T10:00:00Z",
    "updated_date": "2025-12-15T14:30:00Z"
  }
}
```

---

### 3.2 查询备货单详情

**接口地址**: `GET /api/v1/lingxing/stocks/detail`

**请求参数** (Query String):

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| stock_id | string | 是 | 备货单ID | BH20251218001 |
| page | integer | 否 | 页码，默认1 | 1 |
| page_size | integer | 否 | 每页记录数，默认20 | 20 |

**请求示例**:

```bash
curl -X GET "http://localhost:5000/api/v1/lingxing/stocks/detail?stock_id=BH20251218001&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "stock_id": "BH20251218001",
    "stock_name": "美西仓12月补货计划",
    "warehouse_code": "US-WEST-01",
    "warehouse_name": "美西仓库1号",
    "status": "CONFIRMED",
    "total_quantity": 500,
    "total_weight": 125.5,
    "total_volume": 2.35,
    "items": [
      {
        "sku": "TEST-SKU-001",
        "product_name": "测试商品A",
        "quantity": 200,
        "available_quantity": 150,
        "weight": 0.25,
        "dimensions": {
          "length": 20.0,
          "width": 15.0,
          "height": 10.0,
          "unit": "cm"
        }
      }
    ],
    "created_at": "2025-12-18T09:00:00Z",
    "updated_at": "2025-12-18T10:30:00Z"
  }
}
```

---

### 3.3 健康检查

**接口地址**: `GET /api/v1/lingxing/health`

**功能**: 测试领星API配置是否正确，连接是否正常

**请求示例**:

```bash
curl -X GET "http://localhost:5000/api/v1/lingxing/health" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "connected",
    "is_healthy": true,
    "message": "领星API连接正常"
  }
}
```

---

## 前端集成示例

### Vue 3 + TypeScript

在 `frontend/apps/web-antd/src/api/lingxing.ts` 中创建API调用函数：

```typescript
import { request } from '@vben/request';

/**
 * 发货单详情响应
 */
export interface ShipmentDetail {
  shipment_id: string;
  shipment_name: string;
  destination_fulfillment_center_id: string;
  shipment_status: string;
  ship_from_address: {
    name: string;
    address_line1: string;
    city: string;
    state_or_province: string;
    country_code: string;
    postal_code: string;
  };
  items: Array<{
    sku: string;
    fnsku: string;
    quantity_shipped: number;
    quantity_received: number;
    quantity_in_case: number;
  }>;
  total_units: number;
  created_date: string;
  updated_date: string;
}

/**
 * 备货单详情响应
 */
export interface StockDetail {
  stock_id: string;
  stock_name: string;
  warehouse_code: string;
  warehouse_name: string;
  status: string;
  total_quantity: number;
  total_weight: number;
  total_volume: number;
  items: Array<{
    sku: string;
    product_name: string;
    quantity: number;
    available_quantity: number;
    weight: number;
    dimensions: {
      length: number;
      width: number;
      height: number;
      unit: string;
    };
  }>;
  created_at: string;
  updated_at: string;
}

/**
 * 查询发货单详情
 */
export function getShipmentDetail(params: {
  shipment_id: string;
  page?: number;
  page_size?: number;
}) {
  return request<ShipmentDetail>({
    url: '/api/v1/lingxing/shipments/detail',
    method: 'GET',
    params,
  });
}

/**
 * 查询备货单详情
 */
export function getStockDetail(params: {
  stock_id: string;
  page?: number;
  page_size?: number;
}) {
  return request<StockDetail>({
    url: '/api/v1/lingxing/stocks/detail',
    method: 'GET',
    params,
  });
}

/**
 * 健康检查
 */
export function checkLingxingHealth() {
  return request<{
    status: string;
    is_healthy: boolean;
    message: string;
  }>({
    url: '/api/v1/lingxing/health',
    method: 'GET',
  });
}
```

### 组件中使用

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { getShipmentDetail, type ShipmentDetail } from '#/api/lingxing';

const shipmentData = ref<ShipmentDetail>();
const loading = ref(false);

async function loadShipment(shipmentId: string) {
  loading.value = true;
  try {
    shipmentData.value = await getShipmentDetail({
      shipment_id: shipmentId,
      page: 1,
      page_size: 20,
    });
  } catch (error) {
    console.error('查询发货单失败:', error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div v-if="shipmentData">
    <h3>{{ shipmentData.shipment_name }}</h3>
    <p>状态: {{ shipmentData.shipment_status }}</p>
    <p>总件数: {{ shipmentData.total_units }}</p>
  </div>
</template>
```

---

## 错误处理

### 常见错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 400 | 参数错误 | 检查必填参数是否完整 |
| 401 | 认证失败 | 检查JWT Token是否有效 |
| 403 | 权限不足 | 联系管理员分配权限 |
| 404 | 数据不存在 | 检查shipment_id或stock_id是否正确 |
| 500 | 系统异常 | 查看后端日志或联系技术支持 |

### 领星API错误

当调用领星API失败时，后端会返回以下格式的错误：

```json
{
  "code": 400,
  "message": "领星API错误: 签名错误",
  "data": null
}
```

**常见领星错误**:
- `签名错误` - 检查 `LINGXING_APP_KEY` 和 `LINGXING_APP_SECRET` 是否正确
- `时间戳过期` - 服务器时间与领星服务器时间误差超过5分钟，同步服务器时间
- `数据不存在` - 检查ID是否正确
- `权限不足` - 联系领星开通相应API权限

---

## 日志排查

后端日志位于 `backend/logs/app.log`，可以通过以下命令查看：

```bash
# 查看最新日志
docker compose exec backend tail -f logs/app.log

# 搜索领星相关日志
docker compose exec backend grep "领星" logs/app.log

# 搜索错误日志
docker compose exec backend grep "ERROR" logs/app.log | grep lingxing
```

---

## 性能优化建议

### 1. 数据缓存

对于状态为 `CLOSED`（发货单）或 `ARRIVED`（备货单）的数据，可以缓存：

```python
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=3600)  # 缓存1小时
def get_closed_shipment(shipment_id: str):
    return LingxingService.get_shipment_detail(shipment_id)
```

### 2. 异步处理

对于批量同步任务，使用 Celery 异步执行：

```python
from app.tasks import celery

@celery.task
def sync_shipment_batch(shipment_ids: list):
    for sid in shipment_ids:
        data = LingxingService.get_shipment_detail(sid)
        # 保存到数据库...
```

### 3. 限流保护

领星API有频率限制，建议在前端增加防抖/节流：

```typescript
import { debounce } from 'lodash-es';

const debouncedSearch = debounce(async (shipmentId: string) => {
  await loadShipment(shipmentId);
}, 500);
```

---

## 常见问题（FAQ）

**Q1: 配置完成后接口返回"领星API配置不完整"？**

A: 检查 `.env` 文件中的 `LINGXING_APP_KEY` 和 `LINGXING_APP_SECRET` 是否已正确设置，并重启后端服务。

**Q2: 如何在本地开发环境测试？**

A: 确保Docker容器已启动，然后访问 `http://localhost:5000/api/v1/lingxing/health` 测试连接。

**Q3: 权限初始化后，前端仍然无法访问接口？**

A: 需要在系统管理后台为当前用户的角色分配相应权限（`lingxing:*`）。

**Q4: 领星API响应很慢怎么办？**

A: 可以调整 `LINGXING_TIMEOUT` 参数，或者使用异步任务处理大批量数据同步。

**Q5: 如何查看Swagger文档？**

A: 启动后端后访问 `http://localhost:5000/docs`，可以看到完整的API文档和测试界面。

---

## 相关文档

- [领星API集成方案](./领星API集成方案.md) - 详细的技术实现方案
- [领星API官方文档](https://apidoc.lingxing.com) - 领星官方API文档
- [IS-Vue-Admin项目开发规范](./project.md) - 项目整体开发规范

---

## 技术支持

如有问题，请联系：
- 技术支持: 查看项目 Issues
- 领星API问题: https://open.lingxing.com（领星开发者中心）

