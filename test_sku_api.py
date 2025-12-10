#!/usr/bin/env python3
"""
SKU API 测试脚本
用于验证SKU列表和详情API是否正常工作
"""

import requests
import json
import sys

# API配置
BASE_URL = "http://localhost:5000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    # 注意：实际使用时需要有效的JWT Token
    # "Authorization": "Bearer YOUR_TOKEN_HERE"
}

def test_sku_list_api():
    """测试SKU列表API"""
    print("=== 测试SKU列表API ===")
    
    try:
        # 测试基础列表查询
        response = requests.get(
            f"{BASE_URL}/products/variants",
            params={"page": 1, "per_page": 10},
            headers=HEADERS
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get('code') == 0:
                items = data.get('data', {}).get('items', [])
                print(f"获取到 {len(items)} 个SKU")
                
                # 显示前几个SKU
                for i, sku in enumerate(items[:3]):
                    print(f"  {i+1}. SKU: {sku.get('sku')}, 产品: {sku.get('product_name')}")
                
                return True
            else:
                print(f"API返回错误: {data.get('message')}")
                return False
        else:
            print(f"请求失败: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("连接失败，请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

def test_sku_detail_api(sku_code=None):
    """测试SKU详情API"""
    print("\n=== 测试SKU详情API ===")
    
    # 如果没有提供SKU编码，先获取一个
    if not sku_code:
        # 先获取SKU列表
        response = requests.get(
            f"{BASE_URL}/products/variants",
            params={"page": 1, "per_page": 1},
            headers=HEADERS
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                items = data.get('data', {}).get('items', [])
                if items:
                    sku_code = items[0].get('sku')
                else:
                    print("没有找到SKU数据")
                    return False
            else:
                print("无法获取SKU列表")
                return False
        else:
            print("无法获取SKU列表")
            return False
    
    print(f"测试SKU: {sku_code}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/products/variants/{sku_code}",
            headers=HEADERS
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get('code') == 0:
                sku_detail = data.get('data', {})
                print(f"SKU详情获取成功:")
                print(f"  - SKU编码: {sku_detail.get('sku')}")
                print(f"  - 特征码: {sku_detail.get('feature_code')}")
                print(f"  - 产品名称: {sku_detail.get('product_name')}")
                print(f"  - 分类: {sku_detail.get('category_name')}")
                print(f"  - 状态: {'启用' if sku_detail.get('is_active') else '停用'}")
                
                # 显示编码规则
                coding_rules = sku_detail.get('coding_rules', {})
                if coding_rules:
                    print(f"  - 编码规则:")
                    print(f"    * 类目码: {coding_rules.get('category_code')}")
                    print(f"    * 车型码: {coding_rules.get('vehicle_code')}")
                    print(f"    * 流水号: {coding_rules.get('serial')}")
                    print(f"    * 属性后缀: {coding_rules.get('suffix')}")
                
                return True
            else:
                print(f"API返回错误: {data.get('message')}")
                return False
        elif response.status_code == 404:
            print(f"SKU {sku_code} 不存在")
            return False
        else:
            print(f"请求失败: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("连接失败，请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

def test_sku_filter_api():
    """测试SKU筛选API"""
    print("\n=== 测试SKU筛选API ===")
    
    test_cases = [
        {"name": "按分类筛选", "params": {"category_id": 1, "page": 1, "per_page": 5}},
        {"name": "按状态筛选", "params": {"is_active": "true", "page": 1, "per_page": 5}},
        {"name": "搜索关键词", "params": {"q": "test", "page": 1, "per_page": 5}},
    ]
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"参数: {test_case['params']}")
        
        try:
            response = requests.get(
                f"{BASE_URL}/products/variants",
                params=test_case['params'],
                headers=HEADERS
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    items = data.get('data', {}).get('items', [])
                    print(f"  结果: 获取到 {len(items)} 个SKU")
                else:
                    print(f"  结果: API错误 - {data.get('message')}")
            else:
                print(f"  结果: 请求失败 - {response.status_code}")
                
        except Exception as e:
            print(f"  结果: 测试失败 - {e}")

def main():
    """主测试函数"""
    print("SKU API 测试开始")
    print("=" * 50)
    
    # 测试SKU列表API
    list_success = test_sku_list_api()
    
    # 测试SKU详情API
    detail_success = False
    if list_success:
        detail_success = test_sku_detail_api()
    
    # 测试筛选功能
    test_sku_filter_api()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"  SKU列表API: {'✓ 通过' if list_success else '✗ 失败'}")
    print(f"  SKU详情API: {'✓ 通过' if detail_success else '✗ 失败'}")
    
    if list_success and detail_success:
        print("\n✅ SKU API 测试基本通过")
        return 0
    else:
        print("\n❌ SKU API 测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
