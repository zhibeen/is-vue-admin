# 采购主体字段扩展 - 数据库迁移步骤

## 📋 变更说明

扩展了 `sys_companies` 表的字段，新增了以下信息：
- 基础信息：法定名称、简称、英文名称、公司类型、状态
- 证照信息：统一社会信用代码、营业执照信息、经营范围
- 地址信息：注册地址、经营地址、邮编
- 联系信息：联系人、电话、邮箱、传真
- 财务信息：银行账户列表、税率、税务登记日期
- 跨境业务：海关编码、检验检疫代码、外贸经营者备案号等
- 资质证照：进出口许可证、特殊资质列表
- 业务配置：默认币种、付款条款、信用额度、结算周期
- 附件与备注：附件列表、备注信息
- 审计字段：创建人、更新人、更新时间

## 🚀 执行步骤

### 1. 进入后端容器
```bash
docker compose exec backend bash
```

### 2. 生成迁移文件
```bash
flask db migrate -m "扩展采购主体字段"
```

### 3. 检查生成的迁移文件
```bash
# 查看最新的迁移文件
ls -lt migrations/versions/
```

### 4. 应用迁移
```bash
flask db upgrade
```

### 5. 重新生成种子数据（包含新的模拟公司数据）
```bash
flask seed-db
```

## ⚠️ 注意事项

1. **数据兼容性**：所有新增字段都是 `Optional`，不会影响现有数据
2. **字段变更**：原 `name` 字段改为 `legal_name`（法定名称）
3. **模拟数据**：seed-db 命令会创建3个完整的采购主体示例数据

## 🔍 验证步骤

### 检查表结构
```bash
flask shell
```

```python
from app.models.serc.foundation import SysCompany
from app.extensions import db

# 查看所有公司
companies = SysCompany.query.all()
for c in companies:
    print(f"{c.legal_name} - {c.unified_social_credit_code}")

# 查看详细信息
company = SysCompany.query.first()
print(company.bank_accounts)
print(company.cross_border_platform_ids)
```

## 📊 新增的模拟数据

1. **深圳市智贝科技有限公司**
   - 主要采购主体，负责北美市场
   - 有完整的银行账户、跨境平台信息

2. **广州市环球贸易有限公司**
   - 欧洲市场主要采购主体
   - 使用L/C付款方式

3. **上海易达进出口有限公司**
   - 负责欧美市场
   - 有危险品经营资质
   - 外汇账户完整

## 🔄 回滚方案（如需要）

```bash
# 回滚最后一次迁移
flask db downgrade

# 回滚到特定版本
flask db downgrade <revision_id>
```

