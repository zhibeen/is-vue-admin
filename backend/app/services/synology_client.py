import requests
import os
import time
from flask import current_app
from werkzeug.datastructures import FileStorage

class SynologyClient:
    """
    群晖 File Station API 客户端
    封装了登录、文件上传、下载等核心功能
    """
    
    def __init__(self, config=None):
        """
        初始化客户端
        :param config: 可选配置字典，默认使用 current_app.config['NAS_CONFIG']
        """
        self.config = config or current_app.config.get('NAS_CONFIG')
        if not self.config:
            raise ValueError("Synology NAS configuration is missing.")
            
        self.base_url = self.config['host'].rstrip('/')
        self.api_url = f"{self.base_url}/webapi"
        self._sid = None
        self._sid_expire_time = 0
        self.verify_ssl = self.config.get('verify_ssl', False)
        self.timeout = self.config.get('timeout', 30)

    def _get_api_info(self, api_name):
        """
        查询 API 信息 (如 endpoint path, maxVersion)
        注意：生产环境可将此结果缓存，避免每次都请求 query.cgi
        这里为了简化暂未使用 query.cgi，直接使用常见默认路径
        """
        # 实际开发中，auth.cgi 和 entry.cgi 通常是固定的入口
        pass

    def login(self):
        """
        执行登录获取 SID
        """
        url = f"{self.api_url}/auth.cgi"
        params = {
            'api': 'SYNO.API.Auth',
            'version': '3',
            'method': 'login',
            'account': self.config['user'],
            'passwd': self.config['password'],
            'session': 'FileStation',
            'format': 'sid'
        }
        
        try:
            response = requests.get(
                url, 
                params=params, 
                verify=self.verify_ssl, 
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                self._sid = data['data']['sid']
                # 简单设置过期时间，假设 session 有效期较长，这里设为 1 小时后刷新
                self._sid_expire_time = time.time() + 3600
                return True
            else:
                error_code = data.get('error', {}).get('code')
                raise Exception(f"NAS Login failed. Error code: {error_code}")
                
        except Exception as e:
            current_app.logger.error(f"Synology Login Error: {str(e)}")
            raise

    def _ensure_sid(self):
        """确保 SID 有效，过期则重登"""
        if not self._sid or time.time() > self._sid_expire_time:
            self.login()
        return self._sid

    def upload_file(self, file_obj: FileStorage, target_folder_rel: str, filename: str = None):
        """
        上传文件到 NAS
        
        :param file_obj: Flask 的 FileStorage 对象
        :param target_folder_rel: 目标文件夹相对路径 (相对于配置的 root_dir), 例如 "CD2025001/01_contract"
        :param filename: (可选) 重命名文件名，默认使用 file_obj.filename
        :return: 群晖 API 的响应数据
        """
        sid = self._ensure_sid()
        
        # 拼接完整路径
        root_dir = self.config['root_dir'].rstrip('/')
        target_folder_rel = target_folder_rel.strip('/')
        dest_path = f"{root_dir}/{target_folder_rel}"
        
        # 将 _sid 拼接到 URL 中，防止 Body 解析问题
        url = f"{self.api_url}/entry.cgi?_sid={sid}"
        
        # 准备参数
        payload = {
            'api': 'SYNO.FileStation.Upload',
            'version': '2',
            'method': 'upload',
            # '_sid': sid, # URL 中已有，Body 中可省略，避免冲突
            'path': dest_path,
            'create_parents': 'true', # 自动创建父目录
            'overwrite': 'true'       # 同名覆盖
        }
        
        # 处理文件名
        actual_filename = filename or file_obj.filename
        
        # 准备文件流
        # 注意: requests 的 files 参数需要 (filename, fileobj, content_type)
        files = {
            'file': (actual_filename, file_obj.stream, file_obj.content_type or 'application/octet-stream')
        }
        
        try:
            response = requests.post(
                url, 
                data=payload, 
                files=files, 
                verify=self.verify_ssl,
                timeout=self.timeout * 2 # 上传大文件给更多时间
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            current_app.logger.error(f"NAS Upload Error: {str(e)}")
            raise

    def get_file_stream(self, file_path_rel: str):
        """
        获取文件下载流 (用于透传给前端)
        
        :param file_path_rel: 文件相对路径, 例如 "CD2025001/01_contract/contract.pdf"
        :return: requests.Response 对象 (stream=True)
        """
        sid = self._ensure_sid()
        
        root_dir = self.config['root_dir'].rstrip('/')
        full_path = f"{root_dir}/{file_path_rel.strip('/')}"
        
        url = f"{self.api_url}/entry.cgi"
        params = {
            'api': 'SYNO.FileStation.Download',
            'version': '2',
            'method': 'download',
            '_sid': sid,
            'path': full_path,
            'mode': 'download'
        }
        
        try:
            # 开启 stream=True，不立即读取内容到内存
            response = requests.get(
                url, 
                params=params, 
                stream=True, 
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            if response.status_code != 200:
                # 尝试读取错误信息
                try:
                    error_json = response.json()
                    raise Exception(f"Download failed: {error_json}")
                except:
                    response.raise_for_status()
            
            return response
            
        except Exception as e:
            current_app.logger.error(f"NAS Download Error: {str(e)}")
            raise
    
    def download_file_to_buffer(self, file_path_rel: str):
        """
        下载文件到内存缓冲区 (用于PDF合并等场景)
        
        :param file_path_rel: 文件相对路径, 例如 "CD2025001/01_contract/contract.pdf"
        :return: BytesIO 对象，如果文件不存在或下载失败则返回 None
        """
        from io import BytesIO
        
        try:
            response = self.get_file_stream(file_path_rel)
            
            # 读取响应内容到缓冲区
            buffer = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)
            
            buffer.seek(0)
            current_app.logger.info(f"文件已下载到缓冲区: {file_path_rel}, 大小: {buffer.getbuffer().nbytes} bytes")
            return buffer
            
        except Exception as e:
            current_app.logger.error(f"下载文件到缓冲区失败 {file_path_rel}: {str(e)}")
            return None

    def create_folder(self, folder_path_rel: str):
        """
        创建文件夹 (主要用于初始化业务目录结构)
        """
        sid = self._ensure_sid()
        root_dir = self.config['root_dir'].rstrip('/')
        
        # 需要拆分父目录和新文件夹名
        # 例如 full_path = /serc/dev/CD001/Docs
        # API 要求 path=/serc/dev/CD001, name=Docs
        
        full_path = f"{root_dir}/{folder_path_rel.strip('/')}"
        parent_path = os.path.dirname(full_path)
        folder_name = os.path.basename(full_path)
        
        url = f"{self.api_url}/entry.cgi"
        # API params for CreateFolder
        params = {
            'api': 'SYNO.FileStation.CreateFolder',
            'version': '2',
            'method': 'create',
            '_sid': sid,
            'folder_path': f'["{parent_path}"]', # API expects JSON array string for folder_path
            'name': f'["{folder_name}"]',
            'force_parent': 'true'
        }
        
        try:
            response = requests.get(
                url, 
                params=params, 
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            if not data.get('success'):
                 # Ignore if folder already exists (error code 1101 usually means exist, but needs verification)
                 # For now, just log warning
                 current_app.logger.warning(f"Create folder result: {data}")
            return data
        except Exception as e:
            current_app.logger.error(f"NAS Create Folder Error: {str(e)}")
            raise

    def list_files(self, folder_path_rel: str, override_root: str = None):
        """
        列出指定目录下的文件
        :param override_root: 可选，强制指定根目录（用于调试检查根共享文件夹）
        :return: List[Dict] [{'name': 'a.pdf', 'isdir': False, 'size': 1024, 'mtime': 1234567890}]
        """
        sid = self._ensure_sid()
        
        if override_root:
            full_path = override_root
        else:
            root_dir = self.config['root_dir'].rstrip('/')
            full_path = f"{root_dir}/{folder_path_rel.strip('/')}"
        
        url = f"{self.api_url}/entry.cgi"
        params = {
            'api': 'SYNO.FileStation.List',
            'version': '2',
            'method': 'list',
            '_sid': sid,
            'folder_path': full_path,
            'additional': 'size,time'
        }
        
        try:
            response = requests.get(
                url, 
                params=params, 
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                # 如果目录不存在，返回空列表而不是报错
                error_code = data.get('error', {}).get('code')
                if error_code == 408: # No such file or directory
                    return []
                raise Exception(f"NAS List Files failed: {data}")
                
            files = []
            for item in data['data']['files']:
                files.append({
                    'name': item['name'],
                    'isdir': item['isdir'],
                    'path': item['path'], # NAS full path
                    'size': item.get('additional', {}).get('size', 0),
                    'mtime': item.get('additional', {}).get('time', {}).get('mtime', 0)
                })
            return files
            
        except Exception as e:
            current_app.logger.error(f"NAS List Error: {str(e)}")
            raise

    def delete_file(self, file_path_rel: str):
        """
        删除文件
        """
        sid = self._ensure_sid()
        root_dir = self.config['root_dir'].rstrip('/')
        full_path = f"{root_dir}/{file_path_rel.strip('/')}"
        
        url = f"{self.api_url}/entry.cgi"
        params = {
            'api': 'SYNO.FileStation.Delete',
            'version': '2',
            'method': 'delete',
            '_sid': sid,
            'path': full_path
        }
        
        try:
            response = requests.get(
                url, 
                params=params, 
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                raise Exception(f"NAS Delete failed: {data}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"NAS Delete Error: {str(e)}")
            raise
