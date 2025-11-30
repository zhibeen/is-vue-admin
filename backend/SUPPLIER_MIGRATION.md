# 供应商模块更新迁移指南

## 📋 变更说明

我们对 `sys_suppliers` 表进行了重大重构，新增了大量字段以支持精细化的供应链管理。

## 🚀 执行步骤

### 1. 进入后端容器
```bash
docker compose exec backend bash
```

### 2. 生成迁移文件
```bash
flask db migrate -m "Enhance SysSupplier table"
```

### 3. 检查并编辑迁移文件 (重要!)
由于 `code` 字段是 `NOT NULL` 的，如果数据库中已有供应商数据，迁移会失败。
你需要编辑生成的迁移文件（位于 `migrations/versions/` 目录下），在 `upgrade()` 函数中添加数据填充逻辑。

**示例修改**:

```python
def upgrade():
    # 1. 先添加 nullable=True
    with op.batch_alter_table('sys_suppliers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('code', sa.String(length=50), nullable=True))
        # ... 其他字段 ...

    # 2. 填充旧数据
    op.execute("UPDATE sys_suppliers SET code = 'SUP-' || id WHERE code IS NULL")

    # 3. 修改为 nullable=False
    with op.batch_alter_table('sys_suppliers', schema=None) as batch_op:
        batch_op.alter_column('code', nullable=False)
        batch_op.create_unique_constraint('uq_sys_suppliers_code', ['code'])
```

### 4. 应用迁移
```bash
flask db upgrade
```

### 5. 重新生成种子数据
```bash
flask seed-db
```

## 🎨 前端页面

请等待前端代码更新完成后，访问 `/serc/supplier` (路径待定) 查看效果。

