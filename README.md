# MySQL到飞书多维表格同步工具

这是一个用于将MySQL数据库同步到飞书多维表格的工具，支持通过GitHub Actions和HTTP请求触发同步任务。

## 功能特性

- 🔄 自动同步MySQL数据库到飞书多维表格
- 🚀 支持GitHub Actions自动化部署
- 🌐 支持HTTP API触发同步
- 📊 自动创建飞书表格和字段
- 🔒 支持数据去重和增量同步
- 📝 详细的同步日志记录

## 快速开始

### 方法1: 通过GitHub Actions触发同步

#### 1. Repository Dispatch (推荐)

发送POST请求到GitHub API来触发同步：

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/k190513120/mysql_to_base/dispatches \
  -d '{
    "event_type": "sync-mysql-to-base",
    "client_payload": {
      "mysql_host": "your-mysql-host.com",
      "mysql_port": "3306",
      "mysql_username": "your-username",
      "mysql_password": "your-password",
      "mysql_database": "your-database",
      "app_token": "your-feishu-app-token",
      "personal_base_token": "your-feishu-personal-token"
    }
  }'
```

#### 2. 手动触发 (Workflow Dispatch)

1. 访问 [GitHub Actions页面](https://github.com/k190513120/mysql_to_base/actions)
2. 选择 "MySQL to Base Sync" 工作流
3. 点击 "Run workflow"
4. 填入必要的参数
5. 点击 "Run workflow" 开始同步

### 方法2: 本地运行

1. 克隆仓库：
```bash
git clone https://github.com/k190513120/mysql_to_base.git
cd mysql_to_base
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置环境变量：
```bash
export MYSQL_HOST="your-mysql-host.com"
export MYSQL_PORT="3306"
export MYSQL_USERNAME="your-username"
export MYSQL_PASSWORD="your-password"
export MYSQL_DATABASE="your-database"
export APP_TOKEN="your-feishu-app-token"
export PERSONAL_BASE_TOKEN="your-feishu-personal-token"
```

4. 运行同步：
```bash
python api.py
```

## 配置参数说明

### MySQL配置
- `mysql_host`: MySQL服务器地址
- `mysql_port`: MySQL端口号（默认3306）
- `mysql_username`: MySQL用户名
- `mysql_password`: MySQL密码
- `mysql_database`: 要同步的数据库名

### 飞书多维表格配置
- `app_token`: 飞书多维表格的APP_TOKEN
- `personal_base_token`: 飞书多维表格的个人访问令牌

## 获取飞书配置

### 1. 获取APP_TOKEN
1. 打开飞书多维表格
2. 在浏览器地址栏中找到类似 `https://example.feishu.cn/base/FCVLbcAccazgKdsnZEhcKYG7n7g` 的URL
3. `FCVLbcAccazgKdsnZEhcKYG7n7g` 就是APP_TOKEN

### 2. 获取PERSONAL_BASE_TOKEN
1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建应用并获取访问令牌
3. 或使用个人访问令牌

## API接口

### 触发同步

**POST** `/sync` (如果部署为Web服务)

请求体：
```json
{
  "mysql_host": "your-mysql-host.com",
  "mysql_port": 3306,
  "mysql_username": "your-username",
  "mysql_password": "your-password",
  "mysql_database": "your-database",
  "app_token": "your-feishu-app-token",
  "personal_base_token": "your-feishu-personal-token"
}
```

响应：
```json
{
  "success": true,
  "message": "同步完成",
  "results": {
    "table1": true,
    "table2": true
  }
}
```

## 测试示例

使用提供的测试配置：

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/k190513120/mysql_to_base/dispatches \
  -d '{
    "event_type": "sync-mysql-to-base",
    "client_payload": {
      "mysql_host": "rm-zf81e68a31gsqv1c7zo.mysql.kualalumpur.rds.aliyuncs.com",
      "mysql_port": "3306",
      "mysql_username": "writer_readonly",
      "mysql_password": "c*xZ%BEu2VikL%G",
      "mysql_database": "written",
      "app_token": "FCVLbcAccazgKdsnZEhcKYG7n7g",
      "personal_base_token": "pt-uNh9p5Wra6j8XEVOWwF0pZuBOpxfu8K9X5sF2WiZAQAAAkCBYAQAEWvFeL6P"
    }
  }'
```

## 注意事项

1. **权限要求**：确保MySQL用户有读取权限，飞书令牌有创建和编辑表格权限
2. **网络连接**：GitHub Actions需要能够访问你的MySQL服务器
3. **数据安全**：敏感信息建议使用GitHub Secrets存储
4. **频率限制**：避免频繁触发同步，建议设置合理的同步间隔

## 故障排除

### 常见错误

1. **MySQL连接失败**
   - 检查主机地址、端口、用户名和密码
   - 确认网络连接和防火墙设置

2. **飞书API调用失败**
   - 检查APP_TOKEN和PERSONAL_BASE_TOKEN是否正确
   - 确认令牌权限是否足够

3. **字段创建失败**
   - 检查字段名是否符合飞书规范
   - 确认数据类型映射是否正确

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License