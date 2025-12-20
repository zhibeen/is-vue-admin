# 阿里云日志服务（SLS）集成指南

## 📋 目录

1. [为什么需要阿里云 SLS](#为什么需要阿里云-sls)
2. [阿里云 SLS 功能特性](#阿里云-sls-功能特性)
3. [集成步骤](#集成步骤)
4. [AI 日志分析配置](#ai-日志分析配置)
5. [每日报告自动生成](#每日报告自动生成)
6. [成本估算](#成本估算)

---

## 为什么需要阿里云 SLS

### 当前日志系统的局限

**开发环境**（当前方案）：
- ✅ 本地文件日志
- ✅ Docker 容器日志
- ❌ 无法跨服务器聚合
- ❌ 无法长期保存分析
- ❌ 无法实时告警

**生产环境**（推荐 SLS）：
- ✅ 集中式日志管理
- ✅ 实时采集和查询
- ✅ 智能分析和告警
- ✅ 支持 AI 分析
- ✅ 长期存储归档

### 典型使用场景

1. **多服务器日志聚合**
   - 前端服务器 → SLS
   - 后端服务器 → SLS
   - 数据库服务器 → SLS
   - 统一查询分析

2. **智能告警**
   - API 错误率突增 → 自动告警
   - 响应时间异常 → 自动告警
   - 数据库连接失败 → 自动告警

3. **AI 辅助分析**
   - 自动发现异常模式
   - 生成每日运维报告
   - 智能根因分析

---

## 阿里云 SLS 功能特性

### 1. 核心功能

| 功能 | 说明 | 适用场景 |
|------|------|----------|
| **实时采集** | 毫秒级日志采集 | 实时监控 |
| **全文检索** | 支持 SQL 查询 | 快速定位问题 |
| **可视化** | 内置仪表盘 | 运维大屏 |
| **告警** | 自定义告警规则 | 故障通知 |
| **机器学习** | 异常检测 | 智能运维 |

### 2. AI 相关功能

阿里云 SLS 提供以下 AI 能力：

#### ✅ **智能巡检**
- 自动发现日志异常
- 识别错误模式
- 预测潜在问题

#### ✅ **根因分析**
- 故障发生时自动分析原因
- 关联上下游服务
- 生成诊断报告

#### ✅ **智能告警降噪**
- 避免告警风暴
- 合并相似告警
- 智能优先级排序

#### ⚠️ **ChatGPT 集成**（需要配置）
- 自然语言查询日志
- 自动生成分析报告
- 可集成到钉钉/企业微信

---

## 集成步骤

### 步骤 1: 阿里云控制台配置

#### 1.1 创建 SLS 项目和日志库

登录 [阿里云日志服务控制台](https://sls.console.aliyun.com/)：

```bash
# 1. 创建 Project（项目）
名称: is-vue-admin-prod
地域: 选择离您服务器最近的地域
      - 华东1（杭州）
      - 华北2（北京）
      - 华南1（深圳）

# 2. 创建 Logstore（日志库）
名称: app-logs
数据保存时间: 90 天（可根据需求调整）
Shard 数量: 2（默认）
```

#### 1.2 创建索引

在 `app-logs` 日志库中创建索引：

```sql
-- 字段索引配置
timestamp       : text, 分词
level           : text, 不分词
module          : text, 不分词
function        : text, 不分词
message         : text, 分词（使用中文分词）
logger          : text, 不分词
environment     : text, 不分词
user_id         : long
ip_address      : text, 不分词
request_id      : text, 不分词
exception       : text, 分词
```

#### 1.3 获取访问凭证

```bash
# 方式1: 使用主账号 AccessKey（不推荐生产环境）
1. 进入"访问控制" → "用户管理"
2. 创建 RAM 用户
3. 授予 "AliyunLogFullAccess" 权限
4. 获取 AccessKey ID 和 AccessKey Secret

# 方式2: 使用 RAM 角色（推荐）
1. 创建 RAM 角色
2. 授予最小权限策略
3. 使用 STS 临时凭证
```

### 步骤 2: 后端项目配置

#### 2.1 安装依赖

```bash
# 在 backend 目录执行
pip install aliyun-log-python-sdk
```

#### 2.2 更新 requirements.txt

```bash
cd backend
echo "aliyun-log-python-sdk>=0.8.0" >> requirements.txt
```

#### 2.3 配置环境变量

创建生产环境配置文件（参考 `env.example`）：

```bash
# backend/.env.production
FLASK_ENV=production
LOG_LEVEL=INFO

# 启用阿里云 SLS
ENABLE_ALIYUN_SLS=true

# 阿里云凭证
ALIYUN_ACCESS_KEY_ID=<您的 AccessKey ID>
ALIYUN_ACCESS_KEY_SECRET=<您的 AccessKey Secret>

# SLS 配置
ALIYUN_SLS_ENDPOINT=https://cn-hangzhou.log.aliyuncs.com
ALIYUN_SLS_PROJECT=is-vue-admin-prod
ALIYUN_SLS_LOGSTORE=app-logs
```

#### 2.4 Docker Compose 配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: your-registry/is-vue-admin-backend:latest
    environment:
      - FLASK_ENV=production
      - LOG_LEVEL=INFO
      - ENABLE_ALIYUN_SLS=true
      - ALIYUN_ACCESS_KEY_ID=${ALIYUN_ACCESS_KEY_ID}
      - ALIYUN_ACCESS_KEY_SECRET=${ALIYUN_ACCESS_KEY_SECRET}
      - ALIYUN_SLS_ENDPOINT=${ALIYUN_SLS_ENDPOINT}
      - ALIYUN_SLS_PROJECT=${ALIYUN_SLS_PROJECT}
      - ALIYUN_SLS_LOGSTORE=${ALIYUN_SLS_LOGSTORE}
    env_file:
      - .env.production
```

### 步骤 3: 验证日志上传

#### 3.1 启动应用

```bash
# 使用生产配置启动
docker compose -f docker-compose.prod.yml up -d
```

#### 3.2 检查日志

```bash
# 查看应用日志
docker compose logs backend | grep "Aliyun SLS"

# 应该看到类似输出：
# [INFO] Aliyun SLS Handler initialized successfully
```

#### 3.3 在 SLS 控制台验证

1. 进入 SLS 控制台
2. 选择项目 `is-vue-admin-prod`
3. 选择日志库 `app-logs`
4. 点击"查询分析"
5. 输入查询：`* | SELECT * FROM log LIMIT 10`

---

## AI 日志分析配置

### 方案 1: 使用阿里云内置 AI（推荐）

#### 1.1 启用智能巡检

```bash
# 在 SLS 控制台操作
1. 进入"智能巡检" → "创建巡检任务"
2. 配置巡检规则：
   - 巡检频率: 每小时
   - 巡检指标: 错误率、响应时间
   - 异常阈值: 错误率 > 5%

3. 配置通知渠道：
   - 钉钉机器人
   - 企业微信
   - 邮件
   - 短信
```

#### 1.2 配置根因分析

```sql
-- 创建根因分析任务
1. 选择"根因分析" → "创建任务"
2. 配置分析规则：
   - 触发条件: level = ERROR
   - 分析维度: module, function, exception
   - 关联日志: 前后 5 分钟的相关日志

3. 设置输出：
   - 生成诊断报告
   - 发送到钉钉群
```

### 方案 2: 集成 ChatGPT/通义千问

#### 2.1 配置 API

阿里云 SLS 支持集成以下 AI 服务：

```python
# 可选方案
1. 通义千问（阿里云自家，集成最简单）
2. ChatGPT（需要 API Key）
3. 自定义 AI 模型
```

#### 2.2 创建 AI 分析任务

在 SLS 控制台配置：

```yaml
# AI 分析任务配置
name: daily-error-analysis
trigger:
  type: cron
  schedule: "0 8 * * *"  # 每天早上8点

query: |
  * | SELECT 
    level,
    COUNT(*) as count,
    module,
    message
  FROM log
  WHERE __date__ >= '${date.yesterday}'
    AND __date__ < '${date.today}'
    AND level IN ('ERROR', 'WARNING')
  GROUP BY level, module, message
  ORDER BY count DESC
  LIMIT 100

ai_prompt: |
  请分析以下日志数据，生成运维报告：
  1. 总结昨天的错误情况
  2. 找出最频繁的错误及原因
  3. 提供优化建议
  4. 评估系统健康度（0-100分）

output:
  - type: dingtalk
    webhook: https://oapi.dingtalk.com/robot/send?access_token=xxx
  - type: email
    recipients: ["ops@example.com"]
```

---

## 每日报告自动生成

### 方案 1: 使用 SLS 定时 SQL + AI

#### 1.1 创建定时 SQL 任务

```sql
-- 任务名称: daily-summary-report
-- 执行时间: 每天 08:00

-- 查询昨日日志统计
SELECT 
  '系统概览' AS section,
  COUNT(*) AS total_logs,
  COUNT_IF(level = 'ERROR') AS error_count,
  COUNT_IF(level = 'WARNING') AS warning_count,
  COUNT_IF(level = 'INFO') AS info_count,
  ROUND(COUNT_IF(level = 'ERROR') * 100.0 / COUNT(*), 2) AS error_rate
FROM log
WHERE __date__ >= '${date.yesterday}' 
  AND __date__ < '${date.today}'

UNION ALL

-- 错误 Top 10
SELECT 
  '错误 Top 10' AS section,
  module AS module,
  message AS message,
  COUNT(*) AS count
FROM log
WHERE __date__ >= '${date.yesterday}' 
  AND __date__ < '${date.today}'
  AND level = 'ERROR'
GROUP BY module, message
ORDER BY count DESC
LIMIT 10

UNION ALL

-- 响应时间分析
SELECT 
  '响应时间分析' AS section,
  module AS module,
  AVG(duration) AS avg_duration,
  MAX(duration) AS max_duration,
  PERCENTILE(duration, 0.95) AS p95_duration
FROM log
WHERE __date__ >= '${date.yesterday}' 
  AND __date__ < '${date.today}'
  AND duration IS NOT NULL
GROUP BY module
```

#### 1.2 配置 AI 生成报告

```yaml
# AI 报告生成配置
ai_analysis:
  model: qwen-turbo  # 或 gpt-4
  
  system_prompt: |
    你是一个专业的运维工程师。根据日志数据生成每日运维报告。
    报告应该包含：
    1. 📊 系统概览（总日志数、错误率等）
    2. ⚠️ 问题总结（主要错误及原因）
    3. 💡 优化建议（针对性建议）
    4. 📈 趋势分析（对比前一天）
    5. ✅ 系统健康评分（0-100）
    
    使用 Markdown 格式，简洁专业。

  output_format: markdown
  
  notification:
    channels:
      - type: dingtalk
        webhook: ${DINGTALK_WEBHOOK}
        at_mobiles: ["13800138000"]
        
      - type: email
        to: ["ops@example.com", "dev@example.com"]
        subject: "IS-Vue-Admin 每日运维报告 - ${date.yesterday}"
```

### 方案 2: 自定义 Python 脚本

创建定时任务脚本：

```python
# backend/scripts/generate_daily_report.py

from aliyun.log import LogClient
from datetime import datetime, timedelta
import os

def generate_daily_report():
    """生成每日日志报告"""
    
    # 初始化 SLS 客户端
    client = LogClient(
        os.getenv('ALIYUN_SLS_ENDPOINT'),
        os.getenv('ALIYUN_ACCESS_KEY_ID'),
        os.getenv('ALIYUN_ACCESS_KEY_SECRET')
    )
    
    project = os.getenv('ALIYUN_SLS_PROJECT')
    logstore = os.getenv('ALIYUN_SLS_LOGSTORE')
    
    # 查询昨天的日志
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    query = f"""
    * | SELECT 
        COUNT(*) as total,
        COUNT_IF(level='ERROR') as errors,
        COUNT_IF(level='WARNING') as warnings
    FROM log
    WHERE __date__ >= '{yesterday}' AND __date__ < '{today}'
    """
    
    response = client.get_log_all(project, logstore, 
        from_time=yesterday, 
        to_time=today,
        query=query
    )
    
    # 调用 AI 生成报告
    report = call_ai_to_analyze(response)
    
    # 发送报告
    send_to_dingtalk(report)
    send_email(report)

if __name__ == '__main__':
    generate_daily_report()
```

配置定时任务（Cron）：

```bash
# /etc/cron.d/daily-report
0 8 * * * docker exec is_admin_backend python /app/scripts/generate_daily_report.py
```

---

## 报告示例

AI 生成的每日报告示例：

```markdown
# IS-Vue-Admin 每日运维报告
**日期**: 2025-12-19  
**生成时间**: 2025-12-20 08:00:00

---

## 📊 系统概览

| 指标 | 数值 | 变化 |
|------|------|------|
| 总日志数 | 15,234 | ⬆️ +12% |
| 错误数 | 89 | ⬇️ -5% |
| 警告数 | 234 | ➡️ 持平 |
| 错误率 | 0.58% | ⬇️ -0.1% |

**健康评分**: 92/100 ✅

---

## ⚠️ 主要问题

### 1. 数据库连接超时（23次）
- **模块**: logistics_statement_service
- **原因**: PostgreSQL 连接池耗尽
- **影响**: 部分查询失败
- **建议**: 增加连接池大小或优化慢查询

### 2. API 请求限流（15次）
- **模块**: lingxing_api
- **原因**: 领星 API 调用频率过高
- **建议**: 实施请求缓存

---

## 💡 优化建议

1. **数据库优化**
   - 添加索引: `logistics_statements.statement_no`
   - 优化查询: 减少 N+1 查询

2. **缓存策略**
   - 对领星 API 响应实施 5 分钟缓存
   - 预计可减少 70% API 调用

3. **告警优化**
   - 建议设置数据库连接数监控
   - 阈值: > 80% 时告警

---

## 📈 趋势分析

- ✅ 错误率持续下降（本周平均 0.6%，上周 0.9%）
- ⚠️ API 响应时间略有上升（P95: 520ms → 580ms）
- ✅ 系统稳定性良好，无重大故障

---

**报告由 AI 自动生成** | [查看详细日志](https://sls.console.aliyun.com/...)
```

---

## 成本估算

### 阿里云 SLS 计费

```bash
# 按量付费（适合初期）
- 数据写入: ¥0.35/GB
- 数据存储: ¥0.002/GB/天
- 索引流量: ¥0.35/GB
- 读取流量: ¥0.20/GB

# 示例估算（每天 1GB 日志）
每月成本 = (0.35 + 0.002×30 + 0.35) × 30 + 少量读取
         ≈ ¥25/月

# 资源包（推荐生产环境）
- 100GB 写入/月: ¥25（原价 ¥35）
- 可节省约 30%
```

### AI 分析成本

```bash
# 通义千问（阿里云）
- 按 Token 计费
- 每日报告约 2000 tokens
- 月成本: ¥10-20

# ChatGPT-4
- 更贵，约 ¥50-100/月
```

**总成本估算**: ¥35-45/月（小规模应用）

---

## 快速开始检查清单

- [ ] 在阿里云创建 SLS Project 和 Logstore
- [ ] 获取 AccessKey ID 和 Secret
- [ ] 安装 `aliyun-log-python-sdk`
- [ ] 配置环境变量（`ENABLE_ALIYUN_SLS=true`）
- [ ] 启动应用并验证日志上传
- [ ] 配置索引和查询
- [ ] 设置智能巡检和告警
- [ ] 配置 AI 每日报告生成
- [ ] 配置通知渠道（钉钉/邮件）

---

## 相关文档

- [阿里云日志服务官方文档](https://help.aliyun.com/product/28958.html)
- [Python SDK 文档](https://github.com/aliyun/aliyun-log-python-sdk)
- [智能巡检使用指南](https://help.aliyun.com/document_detail/...)
- [AI 分析配置指南](https://help.aliyun.com/document_detail/...)

---

**文档版本**: v1.0  
**最后更新**: 2025-12-20  
**维护者**: 运维团队

