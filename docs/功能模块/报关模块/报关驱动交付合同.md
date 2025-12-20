# SERC 报关驱动交付合同实施方案

## 1. 背景与目标

### 1.1 现状分析
当前系统的采购交付合同（`ScmDeliveryContract`）主要依赖手工录入或单一合同导入。然而在实际业务中，前端采购业务由领星 ERP 处理，本系统主要作为“业财税数据中台”。
实际出货场景通常是：多份采购订单汇集为一次出运（一个柜/一票货），形成一份装箱单（Packing List）进行报关。

### 1.2 目标
建立“**以物流事实驱动商流单据**”的逆向推流模式：
1.  **源头录入**：以“报关/装箱单”为切入点，导入一次出运的全部货物明细。
2.  **自动推流**：系统根据明细中的“供应商”字段，自动将一份装箱单拆分为多份“交付合同”。
3.  **单证一致**：确保财务结算的合同数量与实际报关出口的数量严格一致，规避税务风险。

---

## 2. 业务流程设计 (To-Be Process)

### 2.1 核心流程图

```mermaid
graph TD
    User[用户/关务] -->|1. 导入装箱单 Excel| ImportAPI[报关单导入接口]
    
    subgraph SERC系统
        ImportAPI -->|解析 & 校验| Declaration[报关单 (Draft)]
        
        Declaration -->|2. 点击生成合同| SplitEngine[拆分引擎]
        
        SplitEngine -->|按供应商分组| GroupA[供应商 A]
        SplitEngine -->|按供应商分组| GroupB[供应商 B]
        SplitEngine -->|按供应商分组| GroupC[供应商 C]
        
        GroupA -->|匹配采购价| ContractA[交付合同 A (Draft)]
        GroupB -->|匹配采购价| ContractB[交付合同 B (Draft)]
        GroupC -->|匹配采购价| ContractC[交付合同 C (Draft)]
        
        ContractA -->|回写关联ID| Declaration
    end
    
    ContractA -->|3. 财务审核| Finance[财务/采购]
    Finance -->|确认| Approved[合同生效]
```

### 2.2 关键步骤说明

1.  **装箱单导入**：
    *   用户上传包含 `SKU`、`数量`、`供应商`、`箱号`、`净毛重` 的 Excel 文件。
    *   系统生成 `TaxCustomsDeclaration` 记录，状态为 `DRAFT`。
    
2.  **自动拆分 (Split Engine)**：
    *   系统遍历报关单明细，按 `supplier_id` 进行分组。
    *   如果明细中缺少供应商信息，系统尝试通过 `Product` 表的默认供应商进行填充（需完善主数据）。
    
3.  **合同生成**：
    *   **合同编号**：规则建议 `CON-{报关单号}-{供应商后缀}`。
    *   **价格取值**：
        *   报关单通常使用 FOB 美金价。
        *   交付合同需要人民币采购价。
        *   **策略**：系统优先查找该 SKU 在该供应商的历史采购价；若无，则留空或置为 0，由财务后续补录。

---

## 3. 数据模型变更 (Schema Changes)

为支撑上述流程，需对现有模型进行升级。

### 3.1 报关单主表 (`tax_customs_declarations`)

增加物流与源数据相关字段。

```python
class TaxCustomsDeclaration(db.Model):
    # ... 现有字段 ...
    
    # 物流信息 (新增)
    logistics_provider = mapped_column(String(100), comment='物流服务商')
    shipping_no = mapped_column(String(100), comment='提单号/运单号')
    shipping_date = mapped_column(Date, comment='发货日期')
    
    # 源数据追踪 (新增)
    source_type = mapped_column(String(20), default='manual', comment='来源: manual, excel_import, api')
    source_file_url = mapped_column(String(255), comment='原始文件路径')
    
    # 状态扩展
    # status: DRAFT(草稿/已导入), PROCESSING(处理中/已生成合同), DECLARED(已申报)
```

### 3.2 报关单明细表 (`tax_customs_items`)

增加供应商与 SKU 冗余字段，这是拆分合同的基础。

```python
class TaxCustomsItem(db.Model):
    # ... 现有字段 ...
    
    # 关键业务字段 (新增)
    supplier_id = mapped_column(ForeignKey("sys_suppliers.id"), nullable=True, comment='供应商ID')
    sku = mapped_column(String(100), comment='SKU编码(冗余)')
    
    # 装箱信息 (新增)
    box_no = mapped_column(String(50), comment='箱号')
    net_weight = mapped_column(DECIMAL(10, 4), comment='净重(KG)')
    gross_weight = mapped_column(DECIMAL(10, 4), comment='毛重(KG)')
    
    # 关联 (新增)
    supplier = relationship("SysSupplier")
```

### 3.3 交付合同表 (`scm_delivery_contracts`)

利用现有 `source_doc_id` 或增加明确的报关单关联。

```python
class ScmDeliveryContract(db.Model):
    # ... 现有字段 ...
    
    # 关联报关单 (新增/复用)
    # 建议新增 explicit key 以免混淆 source_doc_id (原用于采购订单)
    customs_declaration_id = mapped_column(ForeignKey("tax_customs_declarations.id"), nullable=True)
```

---

## 4. 接口与逻辑设计

### 4.1 导入接口
*   **Endpoint**: `POST /api/v1/tax/declarations/import`
*   **Input**: Excel File (`.xlsx`)
*   **Logic**:
    1.  解析 Excel。
    2.  校验 SKU 是否存在系统。
    3.  校验 供应商 是否存在（支持按名称模糊匹配）。
    4.  创建 `TaxCustomsDeclaration` 及 `TaxCustomsItem`。

### 4.2 推流生成合同接口
*   **Endpoint**: `POST /api/v1/tax/declarations/{id}/generate-contracts`
*   **Logic**:
    ```python
    def generate_contracts(declaration_id):
        items = get_items(declaration_id)
        
        # 1. Group By Supplier
        grouped = group_by(items, 'supplier_id')
        
        generated_ids = []
        
        # 2. Iterate & Create
        for supplier_id, sub_items in grouped.items():
            # 创建合同头
            contract = create_contract_header(supplier_id, declaration_info)
            
            # 创建合同明细
            for item in sub_items:
                price = find_latest_purchase_price(item.sku, supplier_id)
                create_contract_item(contract.id, item, price)
                
            generated_ids.append(contract.id)
            
        # 3. Update Status
        update_declaration_status(declaration_id, 'PROCESSING')
        
        return generated_ids
    ```

## 5. 实施计划

1.  **数据库迁移**：执行 Alembic 迁移，添加字段。
2.  **后端开发**：
    *   实现 Excel 解析服务。
    *   实现 `TaxService` 中的拆分逻辑。
3.  **前端开发**：
    *   报关单列表页：增加“导入”按钮。
    *   报关单详情页：增加“生成交付合同”按钮及关联数据显示。


