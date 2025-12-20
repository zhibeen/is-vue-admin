# SERC 出口退税智能风控系统 - 详细开发实施手册

## 0. 实施指引与规范

### 0.1 文档目的
本手册旨在指导开发人员按照标准化的流程，分步完成 SERC 系统核心模块的编码工作。遵循“后端先行，前端适配”的原则，确保数据模型与业务逻辑的稳健性。

### 0.2 核心原则 (必读)
1.  **架构遵循**: 严格遵守 `backend/app/services/` (业务逻辑) 与 `backend/app/api/` (路由视图) 分离原则。
2.  **响应规范**: 所有 API 返回必须符合 `{ code: 0, message: "success", data: ... }` 结构。
3.  **跳过范围**: 本阶段**不开发**采购订单 (MPO) 相关功能。业务起点为 **L1 交付合同** (支持手工录入或模拟导入)。
4.  **ORM 规范**: 必须使用 SQLAlchemy 2.0 `Mapped[]` 和 `mapped_column()` 语法。
5.  **资金追踪**: 采用**“基于明细的精准追踪法”**，通过中间表实现 L2 结算单与 L1 业务单据的资金状态穿透。

---

## 阶段一：后端开发 (Backend Development)

后端开发按照 DDD 领域划分，顺序为：**基础域 -> 供应链域 -> 资金域 -> 税务域**。

### 1. 基础环境与公共定义

#### 1.1 目录结构初始化
在 `backend/app/` 下建立以下目录结构：
```text
backend/app/
├── models/
│   └── serc/              # SERC 专用模型
│       ├── __init__.py
│       ├── foundation.py  # 基础档案 (Company, Supplier, Product)
│       ├── supply.py      # 供应链 (L1, SourceDoc)
│       ├── finance.py     # 资金 (L2, L3, Pool, Bank)
│       └── tax.py         # 税务 (Invoice, Customs, Risk)
├── schemas/
│   └── serc/              # 序列化校验
├── services/
│   └── serc/              # 业务逻辑服务
└── api/
    └── v1/
        └── serc/          # API 路由 Blueprint
```

#### 1.2 枚举与常量定义 (`app/models/serc/enums.py`)
定义核心状态机：
- `SourceDocType`: `PL_EXPORT` (出口装箱单), `GRN_STOCK` (入库单)
- `ContractStatus` (L1): 待结算, 结算中, 已结算
- `SettlementStatus` (L2资金): 未付, 部分付款, 已结清
- `InvoiceStatus` (L2票据): 未开票, 部分开票, 已开票
- `PaymentPoolStatus`: 待审批, 待支付, 已支付
- `TaxInvoiceStatus`: `Free` (游离), `Reserved` (预占), `Locked` (已申报)

---

### 2. 模块 A: 基础域 (Foundation Domain)

**目标**: 建立多公司、多供应商及商品基础档案，支撑上层业务。

#### 2.1 数据库模型 (`app/models/serc/foundation.py`)
- **Model**: `SysCompany` (采购主体)
    - `id`, `name`, `tax_id`, `bank_info`.
- **Model**: `SysSupplier` (供应商)
    - `id`, `name`, `short_name`, `payment_terms` (账期), `bank_details` (JSONB).
- **Model**: `SysHSCode` (海关编码)
    - `code`, `name`, `refund_rate` (退税率), `effective_date`.
- **Model**: `SysProduct` (SKU基础)
    - `id`, `sku_code`, `internal_name`.
    - `declared_name` (默认报关名), `hs_code_id`.

---

### 3. 模块 B: 供应链交付域 (Supply Domain)

**目标**: 实现“虚实结合”的交付管理，确立法律确权边界。

#### 3.1 数据库模型 (`app/models/serc/supply.py`)
- **Model**: `ScmSourceDoc` (源头单据 - 统一管理 PL/GRN)
    - `id`, `doc_no`, `type` (PL/GRN), `supplier_id`, `event_date`.
    - `tracking_source` (JSONB): 存储外部溯源信息 (e.g., `{"sys": "LX", "po": "PO001"}`).
- **Model**: `ScmDeliveryContract` (**L1 交付合同** - 核心确权表)
    - `id`, `contract_no`, `source_doc_id` (关联源头), `supplier_id`.
    - `total_amount` (Decimal), `status` (待结算/结算中).
- **Model**: `ScmDeliveryItem` (L1 明细)
    - `l1_id`, `product_id`, `confirmed_qty`, `unit_price` (含税).

#### 3.2 业务服务 (`app/services/serc/supply_service.py`)
- `create_manual_contract`: 手工录入 L1，自动生成虚拟 SourceDoc。
- `sync_from_source`: (未来扩展) 从外部 ERP 同步 GRN/PL 并生成 L1。

---

### 4. 模块 C: 资金域 (Finance Domain) - 核心

**目标**: 实现 L1 -> L2 -> L3 的三层解耦与精准资金追踪。

#### 4.1 数据库模型 (`app/models/serc/finance.py`)
- **Model**: `FinSupplyContract` (供货合同 - 税务视图)
    - `id`, `l1_contract_id`, `invoice_name`, `amount`.
    - *作用*: 指导开票，金额需与 L1 一致。
- **Model**: `FinPurchaseSOA` (**L2 结算单** - 债务确权)
    - `id`, `soa_no`, `supplier_id`, `total_payable` (应付).
    - `paid_amount` (已付), `invoiced_amount` (已开票).
    - `status` (Payment: Unpaid/Partial/Paid, Invoice: None/Partial/Full).
- **Model**: `FinPurchaseSOADetail` (**L2 结算单明细** - **关键桥梁**)
    - `id`, `soa_id`, `l1_contract_id`, `amount`.
    - *作用*: **精准追踪法核心**。连接 L2 与 L1，支持查询“某个 L1 合同付了多少钱”。
- **Model**: `FinPaymentPool` (付款池明细)
    - `id`, `soa_id`, `amount`, `type` (Deposit/Balance/Prepay), `status`.
- **Model**: `FinPaymentRequest` (**L3 付款单**)
    - `id`, `request_no`, `total_pay_amount`, `bank_account`.
- **Model**: `FinBankTransaction` (银行流水) & `FinPaymentReconcile` (核销关联).

#### 4.2 业务服务 (`app/services/serc/finance_service.py`)
- `generate_soa(l1_ids)`: 
    1. 创建 `FinPurchaseSOA`。
    2. 创建 `FinPurchaseSOADetail` (记录每个 L1 的金额)。
    3. 锁定 L1 状态。
- `query_l1_payment_status(l1_id)`:
    - *逻辑*: L1 -> L2 Detail -> L2 SOA -> Check `paid_amount` & `status`.

#### 4.3 业务服务 (`app/services/serc/payment_service.py`)
- `push_to_pool(soa_id)`: 将 SOA 拆分为定金/尾款入池。
- `execute_payment(pool_ids)`: 生成 L3，更新 Pool 状态，回调更新 L2 `paid_amount`。

---

### 5. 模块 D: 税务风控域 (Tax Domain)

**目标**: 实现发票管理、报关单管理及智能匹配与风控。

#### 5.1 数据库模型 (`app/models/serc/tax.py`)
- **Model**: `TaxInvoice` (进项发票)
    - `id`, `invoice_no`, `amount`, `soa_id` (关联 L2), `status` (Free/Reserved/Locked).
- **Model**: `TaxCustomsDeclaration` (报关单 - 预报关/正式 合并)
    - `id`, `entry_no`, `status` (Draft/Pre/Official), `fob_total`, `exchange_rate`.
- **Model**: `TaxCustomsItem` (报关明细)
    - `product_id`, `qty`, `usd_price`, `rma_exchange_cost` (换汇成本 - 风控冗余).
- **Model**: `TaxRefundMatch` (匹配关联表)
    - `customs_item_id`, `invoice_item_id`, `matched_qty`.
- **Model**: `SysExchangeRate` (汇率风控配置).

#### 5.2 业务服务 (`app/services/serc/tax_service.py`)
- `calculate_risk(customs_id)`: 计算换汇成本，对比配置阈值，返回阻断/放行。
- `match_engine(customs_id)`: 尝试在 L2 已结清且已开票的范围内，匹配发票。

---

## 阶段二：前端开发 (Frontend Development)

前端基于 `Vue-Vben-Admin 5.0`。

### 1. 基础对接
- API Client: `api/serc/{foundation, supply, finance, tax}.ts`
- Enums: 同步后端状态定义。

### 2. 核心页面
#### 2.1 供应链管理
- **源头单据**: 展示导入的 PL/GRN。
- **交付合同**: 手工录入/源头生成，展示关联的 L2 状态。

#### 2.2 财务中心
- **结算单管理**: 
    - 列表页展示 L2 状态 (Funds/Invoice 进度条)。
    - 详情页展示关联的 **L1 明细** (Table) 和 **付款记录**。
- **付款池**: 看板视图，拖拽或勾选生成付款单。

#### 2.3 税务工作台
- **发票管理**: 录入发票并挂载到 L2。
- **报关单**: 预报关录入，实时显示“换汇成本”风控结果。
- **退税匹配**: 展示自动匹配结果，支持人工调整。

---

## 3. 开发里程碑 (Milestones)

1.  **M1: 基础与供应链** (Week 1)
    - 完成 Foundation 和 Supply 域的 Model/Service/API。
    - 实现 L1 手工录入。
2.  **M2: 资金闭环** (Week 2)
    - 完成 Finance 域。
    - 跑通 L1 -> L2 -> Pool -> L3 -> L2 Update 全流程。
    - 验证“精准追踪”查询逻辑。
3.  **M3: 税务与风控** (Week 3)
    - 完成 Tax 域。
    - 实现换汇成本计算与阻断。
    - 实现简单的退税匹配逻辑。

## 4. 待办事项 (TODO List)

- [ ] **DB Migration**: 编写 Alembic 迁移脚本 (按领域分批提交)。
- [ ] **Seed Data**: 初始化 SysCompany, SysSupplier, SysProduct。
- [ ] **Unit Test**: 重点测试 `finance_service` 的金额计算和状态回写。

## 5. 供应链业务演进 (Roadmap)

### 5.1 资金流与物流分离
当前系统 (V1) 专注于**财务流**管理，即：
- 供应商管理 (SRM)
- 采购合同 (L1) -> 付款计划 -> 资金池 (Payment Pool)

**物流流** (收货/GRN/库存) 暂不在此系统中深度实现，而是定位为**数据接收端**。

### 5.2 外部系统集成 (API Sync)
未来规划中，物流状态将通过 API 与外部 WMS/ERP 系统同步：
- **收货状态 (GRN Status)**: 外部系统推送 `delivery_status` 和 `received_qty`。
- **库存变动**: 外部系统推送库存快照。

本系统将作为**财务结算中心**，依据 API 同步过来的“实收数量”进行对账和付款。