import sys
from app import create_app
from app.extensions import db
from app.models.system import SysDict
from sqlalchemy import text, select, update

app = create_app()

def seed():
    with app.app_context():
        # 1. Check Column
        print("--- Checking Schema ---")
        try:
            db.session.execute(text("SELECT category FROM sys_dictionaries LIMIT 1"))
            print("✅ Column 'category' exists.")
        except Exception as e:
            print(f"❌ Column 'category' MISSING: {e}")
            print("Attempting to add column...")
            try:
                with db.engine.connect() as conn:
                    with conn.begin():
                        conn.execute(text("ALTER TABLE sys_dictionaries ADD COLUMN category VARCHAR(50)"))
                print("✅ Column 'category' added.")
            except Exception as e2:
                print(f"❌ Failed to add column: {e2}")
                return

        # 2. Check Data
        print("\n--- Checking Data ---")
        existing_count = db.session.query(SysDict).count()
        print(f"Current SysDict count: {existing_count}")
        
        dictionaries = [
            # --- 1. 采购与供应商模块 (SRM) ---
            {
                "name": "供应商类型",
                "code": "supplier_type",
                "category": "purchase",
                "description": "用于供应商建档时的类型分类",
                "is_system": True,
                "value_options": [
                    {"label": "生产商", "value": "manufacturer"},
                    {"label": "贸易商", "value": "trader"},
                    {"label": "服务商", "value": "service_provider"}
                ]
            },
            {
                "name": "供应商状态",
                "code": "supplier_status",
                "category": "purchase",
                "description": "控制供应商的业务状态",
                "is_system": True,
                "value_options": [
                    {"label": "活跃", "value": "active"},
                    {"label": "停用", "value": "inactive"},
                    {"label": "潜在", "value": "potential"},
                    {"label": "黑名单", "value": "blacklisted"}
                ]
            },
            {
                "name": "供应商等级",
                "code": "supplier_grade",
                "category": "purchase",
                "description": "供应商绩效评估等级",
                "is_system": True,
                "value_options": [
                    {"label": "战略级", "value": "A"},
                    {"label": "优质", "value": "B"},
                    {"label": "合格", "value": "C"},
                    {"label": "淘汰", "value": "D"}
                ]
            },
            {
                "name": "纳税人类型",
                "code": "taxpayer_type",
                "category": "purchase",
                "description": "影响开票税率和财务计算",
                "is_system": True,
                "value_options": [
                    {"label": "一般纳税人", "value": "general"},
                    {"label": "小规模纳税人", "value": "small"}
                ]
            },
            # --- 2. 财务与支付模块 (Finance) ---
            {
                "name": "币种",
                "code": "currency",
                "category": "finance",
                "description": "全局通用的货币选择",
                "is_system": True,
                "value_options": [
                    {"label": "人民币", "value": "CNY"},
                    {"label": "美元", "value": "USD"},
                    {"label": "欧元", "value": "EUR"},
                    {"label": "港币", "value": "HKD"}
                ]
            },
            {
                "name": "付款方式",
                "code": "payment_method",
                "category": "finance",
                "description": "采购合同和付款申请中使用",
                "is_system": True,
                "value_options": [
                    {"label": "电汇", "value": "T/T"},
                    {"label": "信用证", "value": "L/C"},
                    {"label": "现金", "value": "Cash"},
                    {"label": "支票", "value": "Check"},
                    {"label": "汇票", "value": "Draft"}
                ]
            },
            {
                "name": "款项类型",
                "code": "payment_type",
                "category": "finance",
                "description": "明确付款的具体用途",
                "is_system": True,
                "value_options": [
                    {"label": "定金", "value": "deposit"},
                    {"label": "尾款", "value": "balance"},
                    {"label": "预付", "value": "prepay"},
                    {"label": "税金", "value": "tax"}
                ]
            },
            {
                "name": "结算状态",
                "code": "settlement_status",
                "category": "finance",
                "description": "付款单据的支付进度",
                "is_system": True,
                "value_options": [
                    {"label": "未付", "value": "unpaid"},
                    {"label": "部分支付", "value": "partial"},
                    {"label": "已结清", "value": "paid"}
                ]
            },
            # --- 3. 产品与供应链模块 (SCM) ---
            {
                "name": "产品质量类型",
                "code": "product_quality_type",
                "category": "product",
                "description": "定义 SKU 的品质属性",
                "is_system": True,
                "value_options": [
                    {"label": "售后件", "value": "Aftermarket"},
                    {"label": "原厂件", "value": "OEM"},
                    {"label": "翻新件", "value": "Refurbished"}
                ]
            },
            {
                "name": "参考码类型",
                "code": "product_code_type",
                "category": "product",
                "description": "产品关联号码的分类",
                "is_system": True,
                "value_options": [
                    {"label": "原厂编码", "value": "OE"},
                    {"label": "代工厂编码", "value": "OEM"},
                    {"label": "北美通用码", "value": "PARTSLINK"}
                ]
            },
            {
                "name": "合同状态",
                "code": "contract_status",
                "category": "supply",
                "description": "交付合同的生命周期状态",
                "is_system": True,
                "value_options": [
                    {"label": "待结算", "value": "pending"},
                    {"label": "结算中", "value": "settling"},
                    {"label": "已结算", "value": "settled"}
                ]
            },
            {
                "name": "单据来源",
                "code": "source_doc_type",
                "category": "supply",
                "description": "追溯业务数据的来源",
                "is_system": True,
                "value_options": [
                    {"label": "出口装箱单", "value": "PL_EXPORT"},
                    {"label": "入库单", "value": "GRN_STOCK"},
                    {"label": "手工录入", "value": "MANUAL"}
                ]
            }
        ]

        print("\n--- Seeding/Updating Data ---")
        for data in dictionaries:
            existing = db.session.scalar(select(SysDict).where(SysDict.code == data['code']))
            if existing:
                print(f"Updating: {data['name']} ({data['code']})")
                existing.name = data['name']
                existing.category = data['category']
                existing.description = data['description']
                existing.is_system = data['is_system']
                existing.value_options = data['value_options']
            else:
                print(f"Creating: {data['name']} ({data['code']})")
                d = SysDict(**data)
                db.session.add(d)
        
        try:
            db.session.commit()
            print("✅ Database Commit Successful!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database Commit Failed: {e}")

        final_count = db.session.query(SysDict).count()
        print(f"Final SysDict count: {final_count}")

if __name__ == "__main__":
    seed()

















