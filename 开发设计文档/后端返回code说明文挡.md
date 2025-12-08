# 后端统一响应代码 (Business Status Codes) 规范

## 1. 设计原则

所有 API 响应均遵循统一格式：
```json
{
  "code": 0,           // 业务状态码
  "message": "success",// 提示信息 (用于前端直接展示或开发调试)
  "data": {}           // 业务数据
}
```

- **Code 0**: 代表业务处理成功。
- **Code > 0**: 代表业务异常或特定状态，前端需根据 Code 进行相应处理（弹窗、跳转、确认等）。
- **Code结构**: 采用 **5位数字** 设计，格式为 `AABBB`。
    - `AA`: **模块编号** (10-99)
    - `BBB`: **具体错误/状态码** (001-999)

## 2. 模块编号分配 (AA)

| 模块编号 | 模块名称 | 说明 |
| :--- | :--- | :--- |
| **0** | **全局成功** | 仅用于 code=0 |
| **10** | **系统级** | 参数校验、数据库异常、服务器内部错误 |
| **20** | **认证授权** | 登录、Token、权限不足 |
| **30** | **产品/分类** | 商品管理、分类结构、属性管理 |
| **40** | **订单/支付** | 订单流程、支付状态 |
| **50** | **用户中心** | 用户信息、部门管理 |

## 3. 详细代码定义

### 3.1 全局与系统 (10xxx)

| Code | 常量名 (建议) | Message (En/Zh) | 说明 | 前端处理建议 |
| :--- | :--- | :--- | :--- | :--- |
| `0` | `SUCCESS` | success | **操作成功** | 正常渲染 `data` |
| `10400` | `BAD_REQUEST` | Bad Request | 请求参数错误 (Schema校验失败) | 弹出 `message` 提示用户 |
| `10404` | `NOT_FOUND` | Not Found | 资源未找到 | 提示资源不存在或刷新列表 |
| `10500` | `INTERNAL_SERVER_ERROR` | Internal Server Error | 系统内部未知错误 | 提示“系统繁忙，请联系管理员” |
| `10001` | `DB_INTEGRITY_ERROR` | DB Integrity Error | 数据库完整性冲突 (如唯一性约束) | 提示重复数据或依赖冲突 |

### 3.2 认证与权限 (20xxx)

| Code | 常量名 (建议) | Message | 说明 | 前端处理建议 |
| :--- | :--- | :--- | :--- | :--- |
| `20101` | `AUTH_INVALID_TOKEN` | Unauthorized | Token 无效或已过期 | **强制登出**，跳转登录页 |
| `20102` | `AUTH_LOGIN_FAILED` | Login Failed | 用户名或密码错误 | 提示错误并保留在登录页 |
| `20403` | `AUTH_FORBIDDEN` | Forbidden | 无权限执行此操作 | 提示“权限不足” |

### 3.3 产品与分类模块 (30xxx)

| Code | 常量名 (建议) | Message | 说明 | 前端处理建议 |
| :--- | :--- | :--- | :--- | :--- |
| `30001` | `PRODUCT_CATEGORY_DUPLICATE` | Category Name Duplicate | 分类名称或编码重复 | 提示修改名称/编码 |
| `30002` | `PRODUCT_DELETE_RESTRICTED` | Delete Restricted | 无法删除 (含子类或关联商品) | 提示原因，禁止删除 |
| **`30010`** | `PRODUCT_CATEGORY_MIGRATION_REQUIRED` | **Migration Required** | **需迁移数据** (修改非空叶子节点为目录时触发) | **弹出确认框**，询问是否自动迁移商品 |

## 4. 后端代码实现参考

建议在 `backend/app/codes.py` 中定义常量，并在 `backend/app/errors.py` 中使用。

### 4.1 常量定义 (`backend/app/codes.py`)

```python
# System (10xxx)
SUCCESS = 0
BAD_REQUEST = 10400
NOT_FOUND = 10404
INTERNAL_ERROR = 10500
DB_INTEGRITY_ERROR = 10001

# Auth (20xxx)
AUTH_INVALID_TOKEN = 20101
AUTH_LOGIN_FAILED = 20102
AUTH_FORBIDDEN = 20403

# Product (30xxx)
PRODUCT_CATEGORY_DUPLICATE = 30001
PRODUCT_DELETE_RESTRICTED = 30002
PRODUCT_CATEGORY_MIGRATION_REQUIRED = 30010
```

### 4.2 异常类定义 (`backend/app/errors.py`)

```python
from apiflask import HTTPError
from app import codes

class BusinessError(HTTPError):
    def __init__(self, message, code=codes.BAD_REQUEST, status_code=400, data=None):
        """
        :param message: 错误提示信息
        :param code: 业务状态码 (从 app.codes 引用)
        :param status_code: HTTP 状态码 (默认 400)
        :param data: 附加数据 (会放入响应的 data 字段中)
        """
        super().__init__(status_code, message)
        self.code = code
        self.data = data
        # APIFlask/Flask 的错误处理机制会自动读取 extra_data
        self.extra_data = {
            'code': code,
            'data': data
        }
```

