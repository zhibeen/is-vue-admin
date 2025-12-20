"""发货单API测试"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from app.models.logistics.shipment import ShipmentOrder, ShipmentOrderItem, ShipmentStatus, ShipmentSource
from app.models.serc.foundation import SysCompany
from app.models.purchase.supplier import SysSupplier
from app.models.product.item import ProductVariant
from app.extensions import db


@pytest.fixture
def company(app):
    """创建测试公司"""
    with app.app_context():
        company = SysCompany(
            legal_name='测试公司',
            short_name='测试',
            code='TEST',
            status='active'
        )
        db.session.add(company)
        db.session.commit()
        return db.session.get(SysCompany, company.id)


@pytest.fixture
def suppliers(app):
    """创建测试供应商"""
    with app.app_context():
        suppliers = []
        for i in range(2):
            supplier = SysSupplier(
                code=f'SUP-{i+1:03d}',
                name=f'供应商{i+1}',
                short_name=f'SUP{i+1}',
                supplier_type='manufacturer',
                status='active',
                currency='CNY'
            )
            db.session.add(supplier)
            suppliers.append(supplier)
        db.session.commit()
        
        # 重新获取以确保在当前session
        return [db.session.get(SysSupplier, s.id) for s in suppliers]


@pytest.fixture
def product_variants(app):
    """创建测试SKU"""
    with app.app_context():
        from app.models.product.item import Product
        
        # 先创建SPU
        spu = Product(
            spu_code='TEST-SPU-001',
            name='测试商品',
            attributes={}
        )
        db.session.add(spu)
        db.session.flush()
        
        # 创建SKU
        variants = []
        for i in range(3):
            variant = ProductVariant(
                product_id=spu.id,
                sku=f'SKU-{i+1:03d}',
                feature_code=f'TEST-SKU-{i+1}',
                specs={'color': 'red'},
                quality_type='Aftermarket',
                is_active=True
            )
            db.session.add(variant)
            variants.append(variant)
        
        db.session.commit()
        
        # 重新获取
        return [db.session.get(ProductVariant, v.id) for v in variants]


@pytest.fixture
def shipment_data(company, suppliers, product_variants):
    """准备发货单测试数据"""
    return {
        'shipper_company_id': company.id,
        'consignee_name': 'US Customer',
        'consignee_address': '123 Main St',
        'consignee_country': 'US',
        'currency': 'CNY',
        'items': [
            {
                'sku': product_variants[0].sku,
                'product_name': '测试商品1',
                'quantity': 100,
                'unit': 'PCS',
                'unit_price': 50.00,
                'tax_rate': 0.13,
                'supplier_id': suppliers[0].id
            },
            {
                'sku': product_variants[1].sku,
                'product_name': '测试商品2',
                'quantity': 200,
                'unit': 'PCS',
                'unit_price': 30.00,
                'tax_rate': 0.13,
                'supplier_id': suppliers[1].id
            }
        ]
    }


class TestShipmentAPI:
    """发货单API测试类"""
    
    def test_create_shipment_success(self, client, token_headers, shipment_data):
        """测试创建发货单成功"""
        response = client.post(
            '/api/v1/logistics/shipments',
            json=shipment_data,
            headers=token_headers
        )
        
        assert response.status_code == 201
        data = response.json['data']
        
        # 验证返回数据
        assert 'id' in data
        assert 'shipment_no' in data
        assert data['shipment_no'].startswith('SH-')
        assert data['status'] == 'draft'
        assert data['consignee_name'] == 'US Customer'
        assert len(data['items']) == 2
        
        # 验证金额计算
        assert 'total_amount' in data
        assert 'total_tax_amount' in data
        assert 'total_amount_with_tax' in data
    
    def test_create_shipment_without_items(self, client, token_headers, company):
        """测试创建发货单时没有明细应该失败"""
        data = {
            'shipper_company_id': company.id,
            'consignee_name': 'Test',
            'currency': 'CNY',
            'items': []
        }
        
        response = client.post(
            '/api/v1/logistics/shipments',
            json=data,
            headers=token_headers
        )
        
        # Schema验证失败会返回422
        assert response.status_code == 422
    
    def test_get_shipment_list(self, client, token_headers, app, company, suppliers, product_variants):
        """测试获取发货单列表"""
        # 先创建几个发货单
        with app.app_context():
            for i in range(3):
                shipment = ShipmentOrder(
                    shipment_no=f'SH-TEST-{i+1:04d}',
                    shipper_company_id=company.id,
                    consignee_name=f'Customer {i+1}',
                    currency='CNY',
                    status='draft'
                )
                db.session.add(shipment)
                db.session.flush()
                
                # 添加明细
                item = ShipmentOrderItem(
                    shipment_id=shipment.id,
                    sku=product_variants[0].sku,
                    product_name='Test Product',
                    quantity=100,
                    unit='PCS',
                    supplier_id=suppliers[0].id
                )
                db.session.add(item)
            
            db.session.commit()
        
        # 测试列表查询
        response = client.get(
            '/api/v1/logistics/shipments',
            headers=token_headers
        )
        
        assert response.status_code == 200
        data = response.json['data']
        assert 'items' in data
        assert 'total' in data
        assert data['total'] >= 3
    
    def test_get_shipment_list_with_search(self, client, token_headers, app, company, suppliers, product_variants):
        """测试搜索发货单"""
        # 创建一个特定的发货单
        with app.app_context():
            shipment = ShipmentOrder(
                shipment_no='SH-SEARCH-0001',
                shipper_company_id=company.id,
                consignee_name='Special Customer',
                currency='CNY',
                status='draft'
            )
            db.session.add(shipment)
            db.session.flush()
            
            item = ShipmentOrderItem(
                shipment_id=shipment.id,
                sku=product_variants[0].sku,
                product_name='Test Product',
                quantity=100,
                unit='PCS',
                supplier_id=suppliers[0].id
            )
            db.session.add(item)
            db.session.commit()
        
        # 搜索
        response = client.get(
            '/api/v1/logistics/shipments?q=SEARCH',
            headers=token_headers
        )
        
        assert response.status_code == 200
        data = response.json['data']
        assert data['total'] >= 1
        
        # 验证搜索结果包含我们创建的发货单
        found = False
        for item in data['items']:
            if 'SEARCH' in item['shipment_no']:
                found = True
                break
        assert found
    
    def test_get_shipment_detail(self, client, token_headers, app, company, suppliers, product_variants):
        """测试获取发货单详情"""
        # 创建发货单
        with app.app_context():
            shipment = ShipmentOrder(
                shipment_no='SH-DETAIL-0001',
                shipper_company_id=company.id,
                consignee_name='Detail Customer',
                consignee_address='123 Detail St',
                currency='CNY',
                status='draft',
                total_amount=Decimal('5000.00')
            )
            db.session.add(shipment)
            db.session.flush()
            
            item = ShipmentOrderItem(
                shipment_id=shipment.id,
                sku=product_variants[0].sku,
                product_name='Detail Product',
                quantity=100,
                unit='PCS',
                unit_price=Decimal('50.00'),
                total_price=Decimal('5000.00'),
                supplier_id=suppliers[0].id
            )
            db.session.add(item)
            db.session.commit()
            
            shipment_id = shipment.id
        
        # 获取详情
        response = client.get(
            f'/api/v1/logistics/shipments/{shipment_id}',
            headers=token_headers
        )
        
        assert response.status_code == 200
        data = response.json['data']
        assert data['shipment_no'] == 'SH-DETAIL-0001'
        assert data['consignee_name'] == 'Detail Customer'
        assert len(data['items']) == 1
    
    def test_update_shipment(self, client, token_headers, app, company, suppliers, product_variants):
        """测试更新发货单"""
        # 创建发货单
        with app.app_context():
            shipment = ShipmentOrder(
                shipment_no='SH-UPDATE-0001',
                shipper_company_id=company.id,
                consignee_name='Old Name',
                currency='CNY',
                status='draft'
            )
            db.session.add(shipment)
            db.session.flush()
            
            item = ShipmentOrderItem(
                shipment_id=shipment.id,
                sku=product_variants[0].sku,
                product_name='Product',
                quantity=100,
                unit='PCS',
                supplier_id=suppliers[0].id
            )
            db.session.add(item)
            db.session.commit()
            
            shipment_id = shipment.id
        
        # 更新
        update_data = {
            'consignee_name': 'New Name',
            'notes': 'Updated notes'
        }
        
        response = client.put(
            f'/api/v1/logistics/shipments/{shipment_id}',
            json=update_data,
            headers=token_headers
        )
        
        if response.status_code != 200:
            print(f"Response: {response.json}")
        
        assert response.status_code == 200
        data = response.json['data']
        assert data['consignee_name'] == 'New Name'
        assert data['notes'] == 'Updated notes'
    
    def test_confirm_shipment(self, client, token_headers, app, company, suppliers, product_variants):
        """测试确认发货单"""
        # 创建发货单
        with app.app_context():
            shipment = ShipmentOrder(
                shipment_no='SH-CONFIRM-0001',
                shipper_company_id=company.id,
                consignee_name='Confirm Customer',
                currency='CNY',
                status='draft'
            )
            db.session.add(shipment)
            db.session.flush()
            
            item = ShipmentOrderItem(
                shipment_id=shipment.id,
                sku=product_variants[0].sku,
                product_name='Product',
                quantity=100,
                unit='PCS',
                supplier_id=suppliers[0].id
            )
            db.session.add(item)
            db.session.commit()
            
            shipment_id = shipment.id
        
        # 确认
        response = client.post(
            f'/api/v1/logistics/shipments/{shipment_id}/confirm',
            headers=token_headers
        )
        
        assert response.status_code == 200
        data = response.json['data']
        assert data['status'] == 'confirmed'
    
    def test_suppliers_preview(self, client, token_headers, app, company, suppliers, product_variants):
        """测试供应商拆分预览"""
        # 创建包含多个供应商商品的发货单
        with app.app_context():
            shipment = ShipmentOrder(
                shipment_no='SH-PREVIEW-0001',
                shipper_company_id=company.id,
                consignee_name='Preview Customer',
                currency='CNY',
                status='draft'
            )
            db.session.add(shipment)
            db.session.flush()
            
            # 供应商1的商品
            item1 = ShipmentOrderItem(
                shipment_id=shipment.id,
                sku=product_variants[0].sku,
                product_name='Product 1',
                quantity=100,
                unit='PCS',
                unit_price=Decimal('50.00'),
                total_price=Decimal('5000.00'),
                supplier_id=suppliers[0].id
            )
            db.session.add(item1)
            
            # 供应商2的商品
            item2 = ShipmentOrderItem(
                shipment_id=shipment.id,
                sku=product_variants[1].sku,
                product_name='Product 2',
                quantity=200,
                unit='PCS',
                unit_price=Decimal('30.00'),
                total_price=Decimal('6000.00'),
                supplier_id=suppliers[1].id
            )
            db.session.add(item2)
            
            db.session.commit()
            shipment_id = shipment.id
        
        # 预览拆分
        response = client.get(
            f'/api/v1/logistics/shipments/{shipment_id}/suppliers-preview',
            headers=token_headers
        )
        
        assert response.status_code == 200
        data = response.json['data']
        
        # 应该有2个供应商
        assert data['supplier_count'] == 2
        assert len(data['suppliers']) == 2
        
        # 验证每个供应商的数据
        for supplier_data in data['suppliers']:
            assert 'supplier_id' in supplier_data
            assert 'supplier_name' in supplier_data
            assert 'items' in supplier_data
            assert 'total_amount' in supplier_data
            assert len(supplier_data['items']) >= 1
    
    def test_delete_shipment_draft(self, client, token_headers, app, company, suppliers, product_variants):
        """测试删除草稿状态的发货单"""
        # 创建草稿发货单
        with app.app_context():
            shipment = ShipmentOrder(
                shipment_no='SH-DELETE-0001',
                shipper_company_id=company.id,
                consignee_name='Delete Customer',
                currency='CNY',
                status='draft'
            )
            db.session.add(shipment)
            db.session.flush()
            
            item = ShipmentOrderItem(
                shipment_id=shipment.id,
                sku=product_variants[0].sku,
                product_name='Product',
                quantity=100,
                unit='PCS',
                supplier_id=suppliers[0].id
            )
            db.session.add(item)
            db.session.commit()
            
            shipment_id = shipment.id
        
        # 删除
        response = client.delete(
            f'/api/v1/logistics/shipments/{shipment_id}',
            headers=token_headers
        )
        
        assert response.status_code == 200
        
        # 验证已删除 (BusinessError返回400而不是404)
        response = client.get(
            f'/api/v1/logistics/shipments/{shipment_id}',
            headers=token_headers
        )
        assert response.status_code == 400
        assert '不存在' in response.json['message']
    
    def test_delete_confirmed_shipment_should_fail(self, client, token_headers, app, company, suppliers, product_variants):
        """测试删除已确认的发货单应该失败"""
        # 创建已确认的发货单
        with app.app_context():
            shipment = ShipmentOrder(
                shipment_no='SH-DELETE-FAIL-0001',
                shipper_company_id=company.id,
                consignee_name='Delete Fail Customer',
                currency='CNY',
                status='confirmed'
            )
            db.session.add(shipment)
            db.session.flush()
            
            item = ShipmentOrderItem(
                shipment_id=shipment.id,
                sku=product_variants[0].sku,
                product_name='Product',
                quantity=100,
                unit='PCS',
                supplier_id=suppliers[0].id
            )
            db.session.add(item)
            db.session.commit()
            
            shipment_id = shipment.id
        
        # 尝试删除
        response = client.delete(
            f'/api/v1/logistics/shipments/{shipment_id}',
            headers=token_headers
        )
        
        assert response.status_code == 400
        assert '草稿状态' in response.json['message']
    
    def test_get_nonexistent_shipment(self, client, token_headers):
        """测试获取不存在的发货单"""
        response = client.get(
            '/api/v1/logistics/shipments/999999',
            headers=token_headers
        )
        
        # BusinessError会返回400
        assert response.status_code == 400
        assert '不存在' in response.json['message']


class TestShipmentService:
    """发货单Service层测试"""
    
    def test_generate_shipment_no(self, app, company):
        """测试发货单号生成"""
        from app.services.logistics.shipment_service import ShipmentService
        
        with app.app_context():
            shipment_no = ShipmentService.generate_shipment_no()
            
            assert shipment_no.startswith('SH-')
            assert len(shipment_no.split('-')) == 3
            
            # 插入一个发货单
            shipment = ShipmentOrder(
                shipment_no=shipment_no,
                shipper_company_id=company.id,
                currency='CNY'
            )
            db.session.add(shipment)
            db.session.commit()
            
            # 再生成一个，应该是递增的
            shipment_no2 = ShipmentService.generate_shipment_no()
            assert shipment_no2 != shipment_no
            assert shipment_no2 > shipment_no
    
    def test_calculate_amounts(self, app):
        """测试金额计算"""
        from app.services.logistics.shipment_service import ShipmentService
        
        with app.app_context():
            items = [
                {
                    'total_price': 100.00,
                    'tax_amount': 13.00,
                    'total_price_with_tax': 113.00
                },
                {
                    'total_price': 200.00,
                    'tax_amount': 26.00,
                    'total_price_with_tax': 226.00
                }
            ]
            
            amounts = ShipmentService.calculate_amounts(items)
            
            assert amounts['total_amount'] == Decimal('300.00')
            assert amounts['total_tax_amount'] == Decimal('39.00')
            assert amounts['total_amount_with_tax'] == Decimal('339.00')

