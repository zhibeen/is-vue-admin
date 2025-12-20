"""领星ERP API服务层

负责与领星API的所有交互，包括：
- 签名生成
- API调用
- 错误处理
- 重试机制
"""
import hashlib
import time
import logging
from typing import Dict, Any, Optional
import requests
from flask import current_app

from app.errors import BusinessError

logger = logging.getLogger(__name__)


class LingxingService:
    """领星API服务类"""
    
    # API端点常量
    SHIPMENT_DETAIL_ENDPOINT = '/api/v1/fba/inbound_shipment/detail'
    STOCK_DETAIL_ENDPOINT = '/api/v1/warehouse/overseas_stock/detail'
    
    @staticmethod
    def _get_config() -> Dict[str, Any]:
        """获取领星API配置"""
        return {
            'base_url': current_app.config.get('LINGXING_API_BASE_URL', 'https://api.lingxing.com'),
            'app_key': current_app.config.get('LINGXING_APP_KEY'),
            'app_secret': current_app.config.get('LINGXING_APP_SECRET'),
            'timeout': current_app.config.get('LINGXING_TIMEOUT', 30),
            'max_retries': current_app.config.get('LINGXING_MAX_RETRIES', 3),
        }
    
    @staticmethod
    def _generate_sign(app_secret: str, data: Dict[str, Any]) -> str:
        """
        生成领星API签名
        
        算法步骤：
        1. 将请求参数按key排序
        2. 拼接成 key1=value1&key2=value2 格式
        3. 前后加上 app_secret
        4. MD5加密后转大写
        
        Args:
            app_secret: 应用密钥
            data: 请求参数字典
            
        Returns:
            str: 签名字符串（32位大写MD5）
        """
        # 排序参数并拼接
        sorted_params = sorted(data.items())
        param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 构造签名原文
        sign_str = f"{app_secret}{param_str}{app_secret}"
        
        # MD5加密并转大写
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
        
        logger.debug(f'生成签名: 参数={param_str}, 签名={sign[:8]}...')
        
        return sign
    
    @staticmethod
    def _call_api(
        endpoint: str,
        data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        调用领星API（包含重试机制）
        
        Args:
            endpoint: API端点路径
            data: 请求参数
            timeout: 超时时间（秒）
            
        Returns:
            Dict: API响应数据
            
        Raises:
            BusinessError: 业务错误或API调用失败
        """
        config = LingxingService._get_config()
        
        # 验证配置
        if not config['app_key'] or not config['app_secret']:
            raise BusinessError('领星API配置不完整，请检查 LINGXING_APP_KEY 和 LINGXING_APP_SECRET')
        
        # 生成时间戳和签名
        timestamp = int(time.time() * 1000)
        sign = LingxingService._generate_sign(config['app_secret'], data)
        
        # 构造请求头
        headers = {
            'Content-Type': 'application/json',
            'app-key': config['app_key'],
            'timestamp': str(timestamp),
            'sign': sign
        }
        
        # 构造完整URL
        url = f"{config['base_url']}{endpoint}"
        
        # 设置超时
        request_timeout = timeout or config['timeout']
        max_retries = config['max_retries']
        
        # 重试逻辑
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                logger.info(f'调用领星API: {endpoint}, 尝试次数: {retry_count + 1}/{max_retries}')
                
                response = requests.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=request_timeout
                )
                
                # 解析响应
                result = response.json()
                
                # 检查业务状态码
                if result.get('code') == 0:
                    logger.info(f'领星API调用成功: {endpoint}')
                    return result.get('data', {})
                
                # 系统异常（5000）可以重试
                elif result.get('code') == 5000:
                    logger.warning(f'领星API系统异常，准备重试: {result.get("message")}')
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count  # 指数退避
                        logger.info(f'等待 {wait_time} 秒后重试...')
                        time.sleep(wait_time)
                    continue
                
                # 其他业务错误不重试
                else:
                    error_code = result.get('code')
                    error_msg = result.get('message', '未知错误')
                    logger.error(f'领星API业务错误: code={error_code}, message={error_msg}')
                    raise BusinessError(
                        f'领星API错误: {error_msg}',
                        code=400,
                        extra={'lingxing_code': error_code}
                    )
                    
            except requests.Timeout as e:
                logger.warning(f'领星API请求超时: {e}')
                retry_count += 1
                last_error = e
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    logger.info(f'等待 {wait_time} 秒后重试...')
                    time.sleep(wait_time)
                continue
                
            except requests.RequestException as e:
                logger.error(f'领星API网络请求失败: {e}')
                raise BusinessError(f'网络请求失败: {str(e)}', code=500)
                
            except ValueError as e:
                logger.error(f'领星API响应解析失败: {e}')
                raise BusinessError('API响应格式错误', code=500)
        
        # 达到最大重试次数
        error_msg = f'调用领星API失败，已达最大重试次数({max_retries})'
        if last_error:
            error_msg += f': {str(last_error)}'
        logger.error(error_msg)
        raise BusinessError(error_msg, code=500)
    
    @staticmethod
    def get_shipment_detail(
        shipment_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        查询发货单详情
        
        Args:
            shipment_id: 发货单ID（亚马逊ShipmentId）
            page: 页码
            page_size: 每页记录数
            
        Returns:
            Dict: 发货单详情数据
            
        Raises:
            BusinessError: 查询失败
        """
        logger.info(f'查询发货单详情: shipment_id={shipment_id}, page={page}, page_size={page_size}')
        
        data = {
            'shipment_id': shipment_id,
            'page': page,
            'page_size': page_size
        }
        
        try:
            result = LingxingService._call_api(
                LingxingService.SHIPMENT_DETAIL_ENDPOINT,
                data
            )
            return result
        except Exception as e:
            logger.error(f'查询发货单详情失败: {e}', extra={
                'shipment_id': shipment_id,
                'error': str(e)
            })
            raise
    
    @staticmethod
    def get_stock_detail(
        stock_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        查询备货单详情
        
        Args:
            stock_id: 备货单ID
            page: 页码
            page_size: 每页记录数
            
        Returns:
            Dict: 备货单详情数据
            
        Raises:
            BusinessError: 查询失败
        """
        logger.info(f'查询备货单详情: stock_id={stock_id}, page={page}, page_size={page_size}')
        
        data = {
            'stock_id': stock_id,
            'page': page,
            'page_size': page_size
        }
        
        try:
            result = LingxingService._call_api(
                LingxingService.STOCK_DETAIL_ENDPOINT,
                data
            )
            return result
        except Exception as e:
            logger.error(f'查询备货单详情失败: {e}', extra={
                'stock_id': stock_id,
                'error': str(e)
            })
            raise
    
    @staticmethod
    def test_connection() -> bool:
        """
        测试领星API连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            config = LingxingService._get_config()
            if not config['app_key'] or not config['app_secret']:
                logger.error('领星API配置不完整')
                return False
            
            # 尝试调用一个简单的API（可以使用测试数据）
            # 注意：这里需要根据实际情况调整测试逻辑
            logger.info('领星API配置检查通过')
            return True
            
        except Exception as e:
            logger.error(f'领星API连接测试失败: {e}')
            return False

