# MySQL到飞书多维表格同步工具

这是一个Python脚本，用于将MySQL数据库表数据同步到飞书多维表格。支持自动创建表格、数据类型映射、增量同步等功能。

## 功能特性

- ✅ **自动表格创建**：为每张MySQL表在飞书多维表格中创建对应的新表
- ✅ **智能数据类型映射**：自动将MySQL数据类型转换为飞书多维表格支持的字段类型
- ✅ **增量同步**：支持记录的创建和更新，避免重复数据
- ✅ **批量操作**：高效的批量数据处理，支持大数据量同步
- ✅ **错误处理**：完善的异常处理和重试机制
- ✅ **日志记录**：详细的同步过程日志，便于问题排查
- ✅ **进度显示**：实时显示同步进度和结果统计

## 环境要求

- Python 3.7+
- MySQL数据库访问权限
- 飞书多维表格访问权限

## 安装依赖

### 1. 安装基础依赖
```bash
pip install PyMySQL>=1.0.2
pip install python-dotenv>=1.0.0
pip install pandas>=1.5.0
```

### 2. 安装飞书Base Open SDK
```bash
pip install https://lf3-static.bytednsdoc.com/obj/eden-cn/lmeh7phbozvhoz/base-open-sdk/baseopensdk-0.0.13-py3-none-any.whl
```

或者使用requirements.txt一键安装：
```bash
pip install -r requirements.txt
# 然后手动安装Base Open SDK
pip install https://lf3-static.bytednsdoc.com/obj/eden-cn/lmeh7phbozvhoz/base-open-sdk/baseopensdk-0.0.13-py3-none-any.whl
```

## 配置说明

### 1. 获取飞书多维表格配置

#### APP_TOKEN（Base ID）
1. 打开你的飞书多维表格
2. 从URL中获取APP_TOKEN：`https://xxx.feishu.cn/base/{APP_TOKEN}/...`
3. 或使用【开发工具】插件快速获取

#### PERSONAL_BASE_TOKEN
1. 在飞书多维表格中点击右上角的"..."
2. 选择"高级设置" → "开发者选项"
3. 创建个人访问令牌（Personal Base Token）
4. 复制生成的token

### 2. MySQL数据库配置

确保你有以下MySQL连接信息：
- 数据库地址
- 端口（通常是3306）
- 用户名
- 密码
- 数据库名

## 使用方法

### 直接运行
```bash
python mysql_to_base_sync.py
```

运行后按提示输入：
- MySQL数据库名
- 飞书多维表格APP_TOKEN
- 飞书多维表格PERSONAL_BASE_TOKEN

### 使用环境变量（推荐）

创建`.env`文件：
```env
# MySQL配置
MYSQL_HOST=rm-zf81e68a31gsqv1c7zo.mysql.kualalumpur.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USERNAME=writer_readonly
MYSQL_PASSWORD=c*xZ%BEu2VikL%G
MYSQL_DATABASE=your_database_name

# 飞书多维表格配置
APP_TOKEN=your_app_token
PERSONAL_BASE_TOKEN=your_personal_base_token
```

然后修改脚本使用环境变量：
```python
from dotenv import load_dotenv
import os

load_dotenv()

mysql_config = MySQLConfig(
    host=os.getenv('MYSQL_HOST'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    username=os.getenv('MYSQL_USERNAME'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE')
)

base_config = BaseConfig(
    app_token=os.getenv('APP_TOKEN'),
    personal_base_token=os.getenv('PERSONAL_BASE_TOKEN')
)
```

## 数据类型映射

| MySQL类型 | 飞书多维表格类型 | 说明 |
|-----------|------------------|------|
| INT, BIGINT, FLOAT, DOUBLE | Number | 数值类型 |
| VARCHAR, TEXT | Text | 文本类型 |
| DATE, DATETIME, TIMESTAMP | DateTime | 日期时间类型 |
| BOOLEAN | Checkbox | 复选框类型 |
| ENUM | SingleSelect | 单选类型 |
| SET | MultiSelect | 多选类型 |
| BLOB | Attachment | 附件类型 |

## 同步逻辑

1. **表创建**：检查飞书多维表格中是否存在同名表，不存在则自动创建
2. **数据同步**：
   - 获取MySQL表数据
   - 转换数据类型
   - 检查记录是否已存在（基于字段值哈希）
   - 新记录：批量创建
   - 已存在记录：批量更新
3. **错误处理**：记录详细错误信息，支持部分失败继续执行

## 日志文件

同步过程会生成`sync.log`日志文件，包含：
- 连接状态
- 同步进度
- 错误信息
- 性能统计

## 注意事项

1. **API限制**：飞书多维表格API有频率限制（2QPS），脚本已内置延迟处理
2. **数据量**：大数据量同步建议分批进行，避免超时
3. **权限**：确保MySQL用户有读取权限，飞书token有写入权限
4. **备份**：建议在同步前备份重要数据
5. **网络**：确保网络连接稳定，支持访问飞书API

## 故障排除

### 常见错误

1. **MySQL连接失败**
   - 检查网络连接
   - 验证数据库地址、端口、用户名、密码
   - 确认数据库存在

2. **飞书API调用失败**
   - 检查APP_TOKEN和PERSONAL_BASE_TOKEN是否正确
   - 确认token权限是否足够
   - 检查网络是否能访问飞书API

3. **数据类型转换错误**
   - 查看日志文件了解具体错误
   - 检查MySQL表结构是否包含不支持的数据类型

### 性能优化

1. **批量大小**：可调整`batch_size`参数优化性能
2. **并发控制**：避免同时运行多个同步任务
3. **增量同步**：定期运行脚本，利用增量同步减少数据传输

## 开发说明

### 项目结构
```
mysql_to_base_sync.py    # 主程序文件
requirements.txt         # 依赖包列表
README.md               # 使用说明
sync.log                # 同步日志（运行后生成）
.env                    # 环境变量配置（可选）
```

### 核心类说明

- `MySQLConfig`: MySQL数据库配置
- `BaseConfig`: 飞书多维表格配置
- `DataTypeMapper`: 数据类型映射器
- `MySQLToBaseSync`: 主同步器类

## 许可证

本项目仅供学习和内部使用，请遵守相关服务的使用条款。

## 支持

如有问题，请查看日志文件或联系开发者。