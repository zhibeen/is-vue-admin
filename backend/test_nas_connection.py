import os
import sys
import unittest
import io
import requests
from flask import Flask
from werkzeug.datastructures import FileStorage

# 尝试加载 env_config (如果 python-dotenv 已安装)
try:
    from dotenv import load_dotenv
    # 指向项目根目录的 env_config
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env_config')
    load_dotenv(env_path)
except ImportError:
    pass

from app.config import config
from app.services.synology_client import SynologyClient

def create_test_app():
    app = Flask(__name__)
    
    # 构造测试配置 - 强制读取环境变量
    nas_config = {
        'host': os.getenv('SYNOLOGY_NAS_HOST'),
        'user': os.getenv('SYNOLOGY_NAS_USER'),
        'password': os.getenv('SYNOLOGY_NAS_PASSWORD'),
        'verify_ssl': os.getenv('SYNOLOGY_NAS_VERIFY_SSL', 'False').lower() in ('true', '1', 't'),
        'timeout': int(os.getenv('SYNOLOGY_NAS_TIMEOUT', 30)),
        # 使用专门的测试目录，避免污染 dev 目录
        'root_dir': os.getenv('SYNOLOGY_NAS_BASE_DIR', '/is_admin_files') + '/test_script' 
    }
    
    app.config['NAS_CONFIG'] = nas_config
    return app

class TestSynologyConnection(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        self.config = self.app.config['NAS_CONFIG']
        print(f"\n--- Current NAS Configuration ---")
        print(f"Host: {self.config.get('host')}")
        print(f"User: {self.config.get('user')}")
        print(f"Root Dir: {self.config.get('root_dir')}")
        print("---------------------------------\n")
        
        try:
            self.client = SynologyClient()
        except Exception as e:
            self.fail(f"Client init failed: {e}")

    def tearDown(self):
        self.ctx.pop()

    def test_01_login(self):
        """测试 NAS 登录功能"""
        print("\n[Step 1] Testing Login...")
        try:
            success = self.client.login()
            self.assertTrue(success)
            self.assertIsNotNone(self.client._sid)
            
            # === 新增：打印 SID 方便调试 ===
            print(f"✅ Login Successful!")
            print(f"🔑 SID: {self.client._sid}") 
            print(f"👉 Use this SID for manual testing: {self.config['host']}/webapi/entry.cgi?api=SYNO.FileStation.List&version=2&method=list&folder_path={self.config['root_dir']}&_sid={self.client._sid}")
            # ==============================
            
        except Exception as e:
            self.fail(f"❌ Login Failed: {str(e)}")

    def test_02_upload(self):
        """测试文件上传"""
        print("\n[Step 2] Testing Upload...")
        
        # 创建一个虚拟文件
        file_content = b"This is a test file content created by script."
        file_obj = FileStorage(
            stream=io.BytesIO(file_content),
            filename="test_upload.txt",
            content_type="text/plain"
        )
        
        try:
            # 确保先登录
            self.client.login()

            # --- 诊断步骤：列出所有共享文件夹 ---
            print("\n[Diagnostic] Listing ALL shared folders to verify path...")
            try:
                # 手动构造请求列出根目录
                url = f"{self.client.api_url}/entry.cgi"
                params = {
                    'api': 'SYNO.FileStation.List',
                    'version': '2',
                    'method': 'list_share', # 使用 list_share 专门列出共享文件夹
                    '_sid': self.client._sid
                }
                res = requests.get(url, params=params, verify=self.client.verify_ssl).json()
                
                found_match = False
                if res.get('success'):
                    shares = res['data']['shares']
                    print(f"✅ Found {len(shares)} shared folders:")
                    for share in shares:
                        print(f"   - Name: {share['name']}, Path: {share['path']}")
                        if 'is_admin_files' in share['path'].lower():
                            found_match = True
                            print(f"   >>> FOUND MATCH! Real path is: {share['path']}")
                else:
                    print(f"❌ Failed to list shares: {res}")
            except Exception as e:
                print(f"❌ Exception listing shares: {e}")

            # --- 诊断步骤：检查各级目录是否存在 ---
            print("\n[Diagnostic] Checking folder existence...")
            
            # 1. 检查最顶层共享文件夹 /is_admin_files
            base_root = "/is_admin_files"
            print(f"👉 Checking base shared folder: {base_root}")
            try:
                files = self.client.list_files(folder_path_rel="", override_root=base_root)
                print(f"✅ Base folder {base_root} exists. Content count: {len(files)}")
            except Exception as e:
                print(f"❌ Failed to list base folder {base_root}: {e}")
                
            # 2. 检查配置的 root_dir (例如 /is_admin_files/test_script)
            target_root = self.config['root_dir'] # /is_admin_files/test_script
            print(f"👉 Checking configured root dir: {target_root}")
            
            # 如果是 408，很可能是 test_script 这个文件夹不存在
            # 我们尝试创建它 (注意：create_folder 需要 parent 和 name)
            # parent: /is_admin_files
            # name: test_script
            
            parent_dir = os.path.dirname(target_root) # /is_admin_files
            folder_name = os.path.basename(target_root) # test_script
            
            print(f"👉 Trying to create test folder '{folder_name}' in '{parent_dir}'...")
            
            # 临时 hack 一下 create_folder，使其支持自定义 parent
            # 正常 create_folder 是基于 config['root_dir'] 的，这里我们要基于绝对路径
            
            sid = self.client._sid
            url = f"{self.client.api_url}/entry.cgi"
            params = {
                'api': 'SYNO.FileStation.CreateFolder',
                'version': '2',
                'method': 'create',
                '_sid': sid,
                'folder_path': f'["{parent_dir}"]',
                'name': f'["{folder_name}"]',
                'force_parent': 'true'
            }
            res = requests.get(url, params=params, verify=self.client.verify_ssl).json()
            print(f"Create Folder Result: {res}")
            
            # --- 关键测试：上传到子目录 ---
            # 既然 test_script 创建成功了，我们就在它下面传文件
            print("\n👉 Uploading to subfolder 'unit_tests' (under test_script)...")
            
            # 重新定位 file 指针
            file_obj.seek(0)
            
            target_folder = "unit_tests"
            result = self.client.upload_file(file_obj, target_folder)
            print(f"Upload Subfolder Result: {result}")
            
            if result.get('success'):
                 # 注意: 返回结构可能是 {'data': {'file': 'filename'}} 或 {'data': {'file': {'path': ...}}}
                 # 安全起见只打印整个 data
                 print(f"✅ Upload Successful! Data: {result.get('data')}")
                 self.assertTrue(True)
            else:
                 print(f"❌ Upload Failed: {result}")
                 self.fail(f"Upload failed with error: {result.get('error')}")
            
        except Exception as e:
            self.fail(f"❌ Upload Failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
