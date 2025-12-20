# 发货单模拟数据生成命令

## 快速使用

### 生成模拟数据

```bash
# 生成20条模拟发货单（默认）
docker compose exec backend flask shipment seed-mock

# 生成指定数量
docker compose exec backend flask shipment seed-mock -c 50

# 清除旧数据后生成
docker compose exec backend flask shipment seed-mock --clear -c 30
```

### 查看数据统计

```bash
# 不生成新数据，只查看统计
docker compose exec backend flask shipment seed-mock -c 0
```

### 清除所有模拟数据

```bash
docker compose exec backend flask shipment seed-mock --clear -c 0
```

## 生成的数据特点

### 1. 多样化的数据来源
- 40% 手工录入
- 30% 领星API同步
- 20% Excel导入
- 10% 易仓API同步

### 2. 真实的状态分布
- 30% 草稿（可编辑）
- 40% 已确认（可生成合同）
- 25% 已发货
- 5% 已完成

### 3. 丰富的国家和客户
- 美国（Amazon US、Walmart等）
- 德国（Amazon DE、MediaMarkt等）
- 日本（Amazon JP、Rakuten等）
- 英国（Amazon UK、Tesco等）
- 澳大利亚（Amazon AU、Coles等）
- 法国、加拿大等

### 4. 真实的物流信息
- 多种物流商：DHL、FedEx、UPS、EMS、Maersk等
- 三种运输方式：海运、空运、快递
- 合理的运输时效和日期

### 5. 完整的商品明细
- 每个发货单包含 3-8 个商品
- 随机分配 1-3 个供应商（模拟混合供货）
- 完整的价格、数量、税额计算
- 包含重量、体积等物流信息

## 前端访问

### 1. 列表页面
```
http://localhost:5173/#/logistics/shipment
```

功能：
- 搜索：发货单号、收货人、物流单号
- 筛选：状态、来源、日期范围
- 操作：查看详情、编辑（草稿）、确认、生成合同

### 2. 详情页面
```
http://localhost:5173/#/logistics/shipment/:id
```

显示：
- 基本信息：发货单号、来源、状态
- 发货信息：发货公司、收货人、地址
- 物流信息：物流商、跟踪号、运输方式、重量体积
- 金额信息：总金额、税额、含税总金额
- 关联状态：报关单、交付合同
- 商品明细：SKU、品名、数量、单价、总价等

## 后端API测试

### 查询列表
```bash
curl http://localhost:5555/api/v1/logistics/shipments?page=1&per_page=10
```

### 查询详情
```bash
curl http://localhost:5555/api/v1/logistics/shipments/1
```

### 确认发货单
```bash
curl -X POST http://localhost:5555/api/v1/logistics/shipments/1/confirm \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### 生成交付合同
```bash
curl -X POST http://localhost:5555/api/v1/logistics/shipments/1/generate-contracts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## 数据库查询

```sql
-- 查看所有模拟发货单
SELECT shipment_no, status, source, consignee_name, total_amount_with_tax, created_at
FROM shipment_orders
WHERE notes LIKE '%模拟发货单%'
ORDER BY created_at DESC;

-- 统计各状态数量
SELECT status, COUNT(*) as count
FROM shipment_orders
WHERE notes LIKE '%模拟发货单%'
GROUP BY status;

-- 查看最近的10条
SELECT * FROM shipment_orders
WHERE notes LIKE '%模拟发货单%'
ORDER BY created_at DESC
LIMIT 10;
```

## 注意事项

1. **依赖数据**：需要先有以下数据
   - 公司数据（SysCompany）
   - 供应商数据（SysSupplier）
   - 产品SKU数据（ProductVariant）

2. **数据清理**：使用 `--clear` 参数会删除所有包含"模拟发货单"备注的记录

3. **唯一性**：发货单号是唯一的，重复的单号会被自动跳过

4. **关联生成**：
   - 部分发货单会标记为"已生成报关单"或"已生成合同"
   - 实际关联数据需要通过相应的API创建

## 故障排查

### 问题1：未找到公司数据
```bash
docker compose exec backend flask company seed
```

### 问题2：未找到供应商数据
```bash
docker compose exec backend flask supplier seed
```

### 问题3：未找到产品数据
```bash
docker compose exec backend flask product seed
```

### 问题4：数据库连接失败
检查 Docker 容器状态：
```bash
docker compose ps
docker compose logs backend
```

## 其他命令

### 初始化权限
```bash
docker compose exec backend flask shipment init-permissions
```

### 查看所有命令
```bash
docker compose exec backend flask shipment --help
```

