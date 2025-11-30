# 采购主体模块更新说明

## 📋 更新概览

本次更新完善了采购主体（公司）管理模块，从简单的3个字段扩展到30+个完整字段，覆盖企业管理的各个方面。

---

## ✅ 已完成的工作

### 1. 后端更新

#### 1.1 数据模型扩展 (`backend/app/models/serc/foundation.py`)
- ✅ 扩展 `SysCompany` 模型，新增30+字段
- ✅ 字段分类：基础信息、证照信息、地址信息、联系信息、财务信息、跨境业务、资质证照、业务配置、附件备注、审计字段

#### 1.2 Schema 定义 (`backend/app/schemas/serc/foundation.py`)
- ✅ 创建 `CompanyDetailSchema` - 详细信息展示
- ✅ 更新 `CompanySimpleSchema` - 列表展示
- ✅ 更新 `CompanyCreateSchema` - 创建表单
- ✅ 更新 `CompanyUpdateSchema` - 更新表单
- ✅ 所有字段添加完整的 metadata（description + example）

#### 1.3 API 路由优化 (`backend/app/api/serc/foundation.py`)
- ✅ 添加完整的 `@doc` 装饰器文档
- ✅ 使用新的 Schema 定义
- ✅ 优化返回值结构

#### 1.4 数据迁移 (`backend/migrations/versions/a8d2399048a7_*.py`)
- ✅ 创建安全的数据迁移脚本
- ✅ 自动迁移旧数据：`name` → `legal_name`
- ✅ 处理 NOT NULL 约束问题
- ✅ 添加唯一索引：`unified_social_credit_code`

#### 1.5 种子数据 (`backend/app/cli.py`)
- ✅ 创建3个完整的模拟公司数据
  - 深圳市智贝科技有限公司（北美市场）
  - 广州市环球贸易有限公司（欧洲市场）
  - 上海易达进出口有限公司（欧美市场，含危险品资质）

---

### 2. 前端更新

#### 2.1 TypeScript 类型定义 (`frontend/apps/web-antd/src/api/serc/model.d.ts`)
- ✅ 完整的 `SysCompany` 接口定义
- ✅ 包含所有30+字段的类型定义
- ✅ 嵌套对象类型定义（bank_accounts, special_licenses 等）

#### 2.2 表格页面优化 (`frontend/apps/web-antd/src/views/system/company/index.vue`)
- ✅ **修复字段映射问题**：`name` → `legal_name`
- ✅ **优化表格列设计**：
  - ID、公司名称、简称
  - 统一社会信用代码
  - 联系人、联系电话
  - 默认币种
  - 状态（带颜色标签）
- ✅ **修复 VXE Table 废弃警告**：
  - `refreshOpts` → `refreshOptions`
  - `zoomOpts` → `zoomOptions`
- ✅ 添加状态标签渲染（正常/停用/暂停）
- ✅ 优化表格样式（stripe、border、showOverflow）
- ✅ 添加调试日志

#### 2.3 表单组件重构 (`frontend/apps/web-antd/src/views/system/company/CompanyModal.vue`)
- ✅ **使用 Tabs 分组展示**：
  - **基础信息**：法定名称、简称、英文名称、公司类型、状态
  - **证照信息**：统一社会信用代码、税号、营业执照、税率
  - **联系信息**：地址、联系人、电话、邮箱、传真
  - **跨境资质**：海关编码、检验检疫、外贸备案、外汇账户
  - **业务配置**：默认币种、付款条款、信用额度、结算周期
  - **备注**：备注信息
- ✅ 使用 Ant Design Vue 原生组件
- ✅ 完整的表单验证
- ✅ 支持创建和更新模式
- ✅ 响应式布局（Modal 宽度 900px）

---

## 🎯 解决的问题

### 问题1: 公司名称没有正常加载
**原因**: 后端字段从 `name` 改为 `legal_name`，但前端表格列仍使用 `field: 'name'`  
**解决**: 更新表格列定义为 `field: 'legal_name'`

### 问题2: 表格信息太单一
**原因**: 只显示 ID、名称、税号三个字段  
**解决**: 扩展为8个列：
- ID
- 公司名称（legal_name）
- 简称（short_name）
- 统一社会信用代码
- 联系人
- 联系电话
- 默认币种
- 状态（带颜色标签）

### 问题3: VXE Table 废弃警告
**原因**: VXE Table v4.17+ 版本参数命名变更  
**解决**: 
- `refresh={...}` → `refresh=true` + `refreshOptions={...}`
- `zoom={...}` → `zoom=true` + `zoomOptions={...}`

---

## 📊 数据结构设计

### 核心字段分类

```typescript
interface SysCompany {
  // 1️⃣ 基础信息 (5个字段)
  legal_name: string;           // 法定名称 ✅ 必填
  short_name?: string;          // 简称
  english_name?: string;        // 英文名称
  company_type?: string;        // 公司类型
  status: string;               // 状态 ✅ 必填

  // 2️⃣ 证照信息 (6个字段)
  unified_social_credit_code?: string;  // 统一社会信用代码 (唯一索引)
  tax_id?: string;                      // 纳税人识别号
  business_license_no?: string;         // 营业执照注册号
  business_license_issue_date?: string; // 发证日期
  business_license_expiry_date?: string;// 有效期
  business_scope?: string;              // 经营范围

  // 3️⃣ 地址信息 (3个字段)
  registered_address?: string;   // 注册地址
  business_address?: string;     // 经营地址
  postal_code?: string;          // 邮政编码

  // 4️⃣ 联系信息 (4个字段)
  contact_person?: string;       // 联系人
  contact_phone?: string;        // 联系电话
  contact_email?: string;        // 联系邮箱
  fax?: string;                  // 传真

  // 5️⃣ 财务信息 (3个字段)
  bank_accounts?: BankAccount[]; // 银行账户列表 (JSONB)
  tax_rate?: number;             // 增值税率
  tax_registration_date?: string;// 税务登记日期

  // 6️⃣ 跨境业务 (6个字段)
  customs_code?: string;                 // 海关编码
  customs_registration_no?: string;      // 海关注册登记编号
  inspection_code?: string;              // 检验检疫代码
  foreign_trade_operator_code?: string;  // 对外贸易经营者备案号
  forex_account?: string;                // 外汇账户
  forex_registration_no?: string;        // 外汇登记证号

  // 7️⃣ 资质证照 (3个字段)
  import_export_license_no?: string;     // 进出口许可证号
  import_export_license_expiry?: string; // 许可证有效期
  special_licenses?: License[];          // 特殊资质列表 (JSONB)

  // 8️⃣ 业务配置 (5个字段)
  default_currency?: string;             // 默认币种
  default_payment_term?: string;         // 默认付款条款
  credit_limit?: number;                 // 信用额度
  settlement_cycle?: number;             // 结算周期（天）
  cross_border_platform_ids?: object;    // 跨境平台账号 (JSONB)

  // 9️⃣ 附件与备注 (2个字段)
  attachments?: Attachment[];            // 附件列表 (JSONB)
  notes?: string;                        // 备注

  // 🔟 审计字段 (4个字段)
  created_by?: number;       // 创建人ID
  updated_by?: number;       // 更新人ID
  created_at?: string;       // 创建时间
  updated_at?: string;       // 更新时间
}
```

---

## 🚀 使用说明

### 前端页面访问
访问路径：`/system/company`

### 功能特性
1. **列表展示**：显示所有采购主体，支持刷新、导出、全屏
2. **新增公司**：点击"新增采购主体"按钮，填写表单
3. **编辑公司**：点击表格中的"编辑"按钮
4. **删除公司**：点击"删除"按钮，二次确认
5. **状态管理**：通过颜色标签区分状态（正常/停用/暂停）

### 表单填写建议
- **必填字段**：法定名称、状态
- **推荐填写**：简称、统一社会信用代码、联系人、联系电话
- **跨境业务**：如涉及进出口，需填写海关编码等信息
- **业务配置**：设置默认币种、付款条款等，方便后续业务使用

---

## 🔧 技术亮点

1. **安全的数据迁移**：分步骤处理 NOT NULL 约束，先迁移数据再设置约束
2. **类型安全**：完整的 TypeScript 类型定义
3. **响应式设计**：表格自适应、表单分组、状态标签
4. **用户体验**：
   - 表单使用 Tabs 分组，避免信息过载
   - 状态使用颜色标签，一目了然
   - 表格支持列宽调整、全屏、导出
5. **可扩展性**：JSONB 字段支持灵活的数据结构（银行账户、资质证照等）

---

## 📝 后续优化建议

1. **银行账户管理**：在表单中添加动态表格，支持添加/删除多个银行账户
2. **附件上传**：集成 OSS，支持营业执照等文件上传
3. **数据验证**：
   - 统一社会信用代码格式校验（18位）
   - 手机号格式校验
   - 邮箱格式校验
4. **权限控制**：敏感字段（如信用额度）根据角色权限显示/隐藏
5. **搜索过滤**：添加搜索框，支持按公司名称、信用代码等搜索
6. **批量操作**：支持批量导入、批量修改状态

---

## ✅ 测试检查清单

- [x] 后端 API 文档生成正确（访问 `/docs`）
- [x] 数据库迁移成功执行
- [x] 种子数据正确生成（3个公司）
- [x] 前端表格正常显示公司列表
- [x] 公司名称字段正确映射（legal_name）
- [x] 状态标签颜色正确显示
- [x] 新增公司功能正常
- [x] 编辑公司功能正常
- [x] 删除公司功能正常（带二次确认）
- [x] 表单验证正常（必填字段）
- [x] Tabs 切换正常
- [x] Console 无废弃警告

---

## 🎉 完成！

采购主体模块已全面升级，从简单的基础信息扩展为企业级完整信息管理系统！

