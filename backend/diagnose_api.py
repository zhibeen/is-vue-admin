import requests
import os
from flask import Flask
from app.config import config
from app.services.synology_client import SynologyClient
# 尝试加载 env_config
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env_config')
    load_dotenv(env_path)
except ImportError:
    pass

# 配置
BASE_URL = "http://localhost:5000" # Docker 内部访问
API_URL = f"{BASE_URL}/api/v1"

def test_api_response():
    print(f"--- Testing API Response for Declaration 25 ---")
    
    # 1. Login to get token
    # 假设有一个测试账号，或者我们直接生成一个 token (如果方便的话)
    # 这里为了简单，我们使用模拟的 Token 生成，或者假设我们已经有一个有效的 Token
    # 但由于这是在 Docker 内部运行，我们可以直接调用 Flask app 的 test_client，这样可以绕过 HTTP 认证或者更方便调试
    
    from app import create_app
    from flask_jwt_extended import create_access_token
    
    app = create_app('development')
    
    with app.app_context():
        # 生成一个超级管理员 Token
        # 假设 user_id=1 是管理员
        access_token = create_access_token(identity=1)
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        print(f"Generated Test Token: {access_token[:20]}...")
        
        # 使用 test_client 模拟请求
        client = app.test_client()
        
        print("\nSending GET request to /api/v1/customs/declarations/25/files ...")
        res = client.get('/api/v1/customs/declarations/25/files', headers=headers)
        
        print(f"Status Code: {res.status_code}")
        print(f"Response Data: {res.json}")
        
        if res.status_code == 200:
            data = res.json.get('data')
            if isinstance(data, list):
                print(f"✅ Data is a List with {len(data)} items.")
            elif isinstance(data, dict):
                 print(f"⚠️ Data is a Dict (Wrapper?): {data.keys()}")
                 if 'data' in data:
                     print(f"   -> Inner Data is: {type(data['data'])}")
            else:
                print(f"❌ Data is {type(data)}")

if __name__ == "__main__":
    test_api_response()

