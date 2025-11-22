# IS-Vue-Admin 开发环境指南

## 1. 环境准备 (Prerequisites)
- **Docker Desktop**: 确保已安装并启动。
- **Git**: 用于代码版本管理。
- **阿里云 RDS 白名单**: 确保你当前网络的公网 IP 已添加到数据库白名单中。

## 2. 快速启动 (Quick Start)

### 步骤一：配置文件
确保根目录下存在 `env_config` 文件（Docker 会自动读取此文件作为环境变量）。
*如果没有，请从 `env_config.example` 复制一份并填入数据库信息。*

### 步骤二：启动后端服务
在项目根目录打开终端，执行：
```bash
docker-compose up --build
```
*   首次运行会自动构建镜像，耗时约 1-3 分钟。
*   启动成功后，终端会显示日志 `Running on http://0.0.0.0:5000`。

## 3. 数据库初始化 (DB Initialization)

**首次运行**或**数据模型变更**后，需要进入容器执行以下命令。

### 3.1 进入容器
保持上面的运行窗口不关闭，**新建**一个终端窗口：
```bash
docker exec -it is_admin_backend /bin/bash
```

### 3.2 执行迁移与填充
在容器内部提示符下 (`root@...:/app#`) 执行：

```bash
# 1. 初始化/升级表结构
flask db init      # (仅项目第一次运行时需要，若报错目录已存在请忽略)
flask db migrate -m "Update schema"
flask db upgrade

# 2. 填充模拟数据 (创建默认分类、属性、Admin账号)
flask seed-db
```

### 3.3 退出容器
```bash
exit
```

## 4. 验证运行 (Verification)

打开浏览器访问 Swagger 文档：
👉 **http://localhost:5000/docs**

### 4.1 测试登录 (获取 Token)
1.  找到接口 `POST /api/v1/auth/login`。
2.  使用默认管理员账号：
    - **Username**: `admin`
    - **Password**: `admin123`
3.  点击 Execute，应返回 `access_token`。

### 4.2 测试数据
1.  找到接口 `GET /api/v1/categories/tree`。
2.  点击 Execute，应返回 "汽车照明"、"保险杠" 等树状结构数据。

## 5. 常见问题 (Troubleshooting)

- **Error: DATABASE_URL not set**
  - 检查 `docker-compose.yml` 是否正确配置了 `env_file: - env_config`。
  - 检查 `env_config` 文件是否存在且有内容。

- **Connection refused (Database)**
  - 检查阿里云 RDS 白名单配置。
  - 检查 `DATABASE_URL` 格式是否正确。

- **Port 5000 already in use**
  - 端口被占用，请关闭其他占用 5000 端口的程序，或修改 `docker-compose.yml` 中的映射端口。

