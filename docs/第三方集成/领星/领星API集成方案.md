# 领星ERP API 集成方案

## 1. 概述

本文档描述了 IS-Vue-Admin 系统与领星ERP系统的API集成方案，主要用于获取发货单和备货单数据。

### 1.1 领星API基本信息

- **API文档地址**: https://apidoc.lingxing.com
- **认证方式**: API Key + Secret (需要在领星后台申请)
- **请求协议**: HTTPS
- **数据格式**: JSON

## 2. 接口说明

### 2.1 查询发货单详情 (FBA Inbound Shipment Detail)

#### 接口信息

- **接口地址**: `/api/v1/fba/inbound_shipment/detail`
- **请求方法**: POST
- **功能说明**: 查询亚马逊FBA发货单的详细信息，包括发货计划、商品明细、物流状态等

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| shipment_id | string | 是 | 发货单ID (亚马逊ShipmentId) |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页记录数，默认20，最大100 |

#### 请求示例

```json
{
  "shipment_id": "FBA12345678",
  "page": 1,
  "page_size": 20
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 状态码，0表示成功 |
| message | string | 返回消息 |
| data | object | 发货单数据对象 |

**data 对象结构**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| shipment_id | string | 发货单ID |
| shipment_name | string | 发货单名称 |
| destination_fulfillment_center_id | string | 目标仓库代码 |
| label_prep_type | string | 标签准备类型 |
| shipment_status | string | 发货状态 (WORKING/SHIPPED/RECEIVING/CLOSED等) |
| ship_from_address | object | 发货地址 |
| items | array | 商品明细列表 |
| total_units | integer | 总件数 |
| created_date | string | 创建时间 (ISO 8601格式) |
| updated_date | string | 更新时间 |

**items 数组元素结构**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| sku | string | 商品SKU |
| fnsku | string | 亚马逊仓库SKU |
| quantity_shipped | integer | 已发货数量 |
| quantity_received | integer | 已入库数量 |
| quantity_in_case | integer | 每箱数量 |

#### 响应示例

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

### 2.2 查询备货单详情 (Overseas Stock Detail)

#### 接口信息

- **接口地址**: `/api/v1/warehouse/overseas_stock/detail`
- **请求方法**: POST
- **功能说明**: 查询海外仓备货单详情，包括备货计划、库存分配、商品明细等

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| stock_id | string | 是 | 备货单ID |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页记录数，默认20，最大100 |

#### 请求示例

```json
{
  "stock_id": "BH20251218001",
  "page": 1,
  "page_size": 20
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 状态码，0表示成功 |
| message | string | 返回消息 |
| data | object | 备货单数据对象 |

**data 对象结构**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| stock_id | string | 备货单ID |
| stock_name | string | 备货单名称 |
| warehouse_code | string | 仓库代码 |
| warehouse_name | string | 仓库名称 |
| status | string | 备货状态 (DRAFT/CONFIRMED/IN_TRANSIT/ARRIVED等) |
| total_quantity | integer | 总数量 |
| total_weight | number | 总重量(kg) |
| total_volume | number | 总体积(m³) |
| items | array | 商品明细列表 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

**items 数组元素结构**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| sku | string | 商品SKU |
| product_name | string | 商品名称 |
| quantity | integer | 备货数量 |
| available_quantity | integer | 可用库存 |
| weight | number | 单件重量(kg) |
| dimensions | object | 尺寸信息 |

#### 响应示例

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
      },
      {
        "sku": "TEST-SKU-002",
        "product_name": "测试商品B",
        "quantity": 300,
        "available_quantity": 280,
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

## 3. 认证方式

领星API使用 **签名认证** 机制：

### 3.1 认证参数

所有请求需要在 Header 中包含以下参数：

| Header名 | 说明 |
|----------|------|
| app-key | 应用标识，由领星分配 |
| timestamp | 当前时间戳（毫秒） |
| sign | 请求签名 |

### 3.2 签名算法

```python
import hashlib
import time

def generate_sign(app_key: str, app_secret: str, timestamp: int, data: dict) -> str:
    """
    生成领星API签名
    
    算法步骤：
    1. 将请求参数按key排序
    2. 拼接成 key1=value1&key2=value2 格式
    3. 前后加上 app_secret
    4. MD5加密后转大写
    """
    # 排序参数
    sorted_params = sorted(data.items())
    param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    
    # 构造签名原文
    sign_str = f"{app_secret}{param_str}{app_secret}"
    
    # MD5加密
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    
    return sign
```

### 3.3 请求示例（包含认证）

```python
import requests
import time

app_key = "your_app_key"
app_secret = "your_app_secret"
timestamp = int(time.time() * 1000)

data = {
    "shipment_id": "FBA12345678",
    "page": 1,
    "page_size": 20
}

sign = generate_sign(app_key, app_secret, timestamp, data)

headers = {
    "Content-Type": "application/json",
    "app-key": app_key,
    "timestamp": str(timestamp),
    "sign": sign
}

response = requests.post(
    "https://api.lingxing.com/api/v1/fba/inbound_shipment/detail",
    json=data,
    headers=headers
)
```

---

## 4. 错误码说明

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | - |
| 1000 | 参数错误 | 检查必填参数是否完整 |
| 1001 | 签名错误 | 检查app_key和app_secret是否正确 |
| 1002 | 时间戳过期 | 时间戳误差超过5分钟，同步服务器时间 |
| 2000 | 数据不存在 | 检查shipment_id或stock_id是否正确 |
| 2001 | 权限不足 | 联系领星开通相应API权限 |
| 5000 | 系统异常 | 稍后重试或联系领星技术支持 |

---

## 5. 限流规则

- **频率限制**: 每秒最多10次请求
- **每日配额**: 每天最多100,000次请求
- **并发限制**: 单个app_key最多5个并发请求

**建议**:
- 使用连接池复用HTTP连接
- 实现指数退避重试策略
- 缓存不常变更的数据

---

## 6. 最佳实践

### 6.1 错误处理

```python
def call_lingxing_api(url, data):
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            result = response.json()
            
            if result['code'] == 0:
                return result['data']
            elif result['code'] == 5000:
                # 系统异常，重试
                retry_count += 1
                time.sleep(2 ** retry_count)  # 指数退避
            else:
                # 业务错误，不重试
                raise BusinessError(result['message'])
                
        except requests.Timeout:
            retry_count += 1
            time.sleep(2 ** retry_count)
        except Exception as e:
            raise
    
    raise BusinessError('调用领星API失败，已达最大重试次数')
```

### 6.2 数据缓存

- 发货单状态为 `CLOSED` 后可以缓存
- 备货单状态为 `ARRIVED` 后可以缓存
- 其他状态建议缓存5-15分钟

### 6.3 异步处理

对于批量数据同步，建议使用 Celery 异步任务：

```python
@celery.task
def sync_shipment_from_lingxing(shipment_id: str):
    """异步同步发货单数据"""
    data = call_lingxing_api('/fba/inbound_shipment/detail', {
        'shipment_id': shipment_id
    })
    # 保存到本地数据库
    save_shipment_data(data)
```

---

## 7. IS-Vue-Admin 集成方案

### 7.1 系统架构

```
前端 (Vue3)
    ↓ HTTP Request
后端 API Layer (Flask)
    ↓ Service Call
领星服务层 (LingxingService)
    ↓ HTTP Request
领星ERP API
```

### 7.2 模块说明

- **路由层**: `backend/app/api/lingxing/routes.py` - 接收前端请求
- **服务层**: `backend/app/services/lingxing/lingxing_service.py` - 封装领星API调用
- **Schema层**: `backend/app/schemas/lingxing/` - 定义请求/响应数据结构
- **配置**: `backend/.env` - 存储app_key和app_secret

### 7.3 数据流转

1. 前端发起请求到 `/api/v1/lingxing/shipments/{shipment_id}`
2. 后端路由层验证JWT Token和权限
3. 调用 `LingxingService.get_shipment_detail(shipment_id)`
4. 服务层生成签名并调用领星API
5. 解析响应数据并返回给前端

### 7.4 配置示例

```bash
# backend/.env
LINGXING_API_BASE_URL=https://api.lingxing.com
LINGXING_APP_KEY=your_app_key_here
LINGXING_APP_SECRET=your_app_secret_here
LINGXING_TIMEOUT=30
LINGXING_MAX_RETRIES=3
```

---

## 8. 测试建议

### 8.1 单元测试

```python
def test_generate_sign():
    app_secret = "test_secret"
    data = {"key1": "value1", "key2": "value2"}
    sign = generate_sign("app_key", app_secret, 1234567890000, data)
    assert len(sign) == 32  # MD5固定长度
    assert sign.isupper()   # 必须大写
```

### 8.2 集成测试

- 测试签名生成的正确性
- 测试超时重试机制
- 测试错误码处理
- 使用Mock数据模拟领星API响应

---

## 9. 附录

### 9.1 常用状态枚举

**发货单状态 (shipment_status)**:
- `WORKING` - 工作中
- `SHIPPED` - 已发货
- `IN_TRANSIT` - 运输中
- `DELIVERED` - 已送达
- `RECEIVING` - 入库中
- `CLOSED` - 已完成
- `CANCELLED` - 已取消
- `ERROR` - 异常

**备货单状态 (stock status)**:
- `DRAFT` - 草稿
- `CONFIRMED` - 已确认
- `IN_TRANSIT` - 在途
- `ARRIVED` - 已到货
- `CANCELLED` - 已取消

### 9.2 参考链接

- 领星API官方文档: https://apidoc.lingxing.com
- 领星开发者中心: https://open.lingxing.com

