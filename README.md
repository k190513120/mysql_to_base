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
      "personal_base_token": "your-feishu-personal-token",
      "region": "domestic"
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
export REGION="domestic"
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
- `region`: 区域选择，支持以下值：
  - `domestic`: 国内飞书（默认值）
  - `overseas`: 海外Lark

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
  "personal_base_token": "your-feishu-personal-token",
  "region": "domestic"
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

### 国内飞书同步示例

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
      "personal_base_token": "pt-uNh9p5Wra6j8XEVOWwF0pZuBOpxfu8K9X5sF2WiZAQAAAkCBYAQAEWvFeL6P",
      "region": "domestic"
    }
  }'
```

### 海外Lark同步示例

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
      "app_token": "your-lark-app-token",
      "personal_base_token": "your-lark-personal-token",
      "region": "overseas"
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

### 排查同步重复写入

如果怀疑某次定时任务把记录写重了，看 GitHub Actions 日志里的同步统计：

```bash
gh run view <run_id> --repo k190513120/mysql_to_base --log | grep "同步完成 - 总计"
```

健康表的特征是 `新增: 0` 或一个很小的增量。如果出现 `新增 ≈ 总计`，说明该表在去重映射加载时遇到瞬时错误未被正确处理（已知会触发的飞书错误：`Data not ready, please try again later`、`InternalError` 等）。仓库根目录的 `check_duplicates.py` / `cleanup_duplicates.py` 可用于扫描和清理（按 MySQL 真实主键，含复合主键）。

## 运维脚本

仓库根目录提供两个只在出问题时使用的脚本：

- **`check_duplicates.py`** ：只读扫描每张飞书表按主键的重复情况，输出每表 base 记录数 / 唯一 PK 数 / 多余记录数。
- **`cleanup_duplicates.py`** ：按 MySQL 真实主键（含复合主键）分组，每组保留 record_id 最早的一条、删除其余。默认 DRY-RUN，加 `--execute` 才真正删除。

调用方式：

```bash
python -m venv .venv && source .venv/bin/activate
pip install pymysql python-dotenv
pip install https://lf3-static.bytednsdoc.com/obj/eden-cn/lmeh7phbozvhoz/base-open-sdk/baseopensdk-0.0.13-py3-none-any.whl

# 配置 .env 后
python check_duplicates.py            # 扫描
python cleanup_duplicates.py          # DRY-RUN 计划
python cleanup_duplicates.py --execute  # 真正清理
```

## 更新历史

### 2026-04 同步可靠性修复

历史曾出现"偶发整表数据重复写入"（约 5 万条），根因为两个叠加：

1. **去重映射在拉取失败时返回残缺数据**（`mysql_to_base_sync.py:get_existing_records`）：分页拉飞书已存在记录时，遇到瞬时错误（`Data not ready, please try again later` 等）会 `break` 后返回部分/空映射，导致下游把整张表当成新记录批量插入。
2. **复合主键中间表只取了首列做去重**（`mysql_to_base_sync.py:get_primary_key`）：`(admin_id, role_id)` 之类组合键的中间表（`la_admin_dept` / `la_admin_jobs` / `la_admin_role` / `la_system_role_menu`）会让多条不同 role 的行共用同一个 record_key，反复 update 到同一个 record_id 上，飞书侧关联数据持续丢失。

修复 commit：

- `f2209aa` —— 引入 `_call_with_retry` 指数退避；`get_existing_records` 失败抛异常，`sync_table_data` 捕获后中止该表本次同步；`_batch_create` / `_batch_update` 也接入重试。
- `483805d` —— `get_primary_key` 返回完整主键列表 `List[str]`；新增 `_make_pk_key` 用 `\x1f` 拼组合 key；读写两侧统一使用复合 key 比对。

修任何同步逻辑前请先看这两个 commit 的差异，避免重新引入这两类问题。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License