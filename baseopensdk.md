# BaseOpenSDK（Python）官方文档

## 概述

#### ⻜书开放平台提供了一系列服务端的原子API来实现多元化的功能，其中就包括操作多维表格的数

#### 据。但是这一套流程需要申请开放平台应用，使用开放平台的鉴权体系，对于只想通过服务端脚本快

#### 速操作多维表格的开发者，流程未免显得繁琐。为此，我们新推出了多维表格独立的鉴权体系，开发

#### 者可以在网⻚端获取某个Base的授权码PersonalBaseToken，即可在服务端通过SDK操作

#### Base数据。

#### BaseOpenSDK接口定义和⻜书开放平台OpenAPI完全一致，无需额外的学习成本。我们将所有冗⻓

#### 的逻辑内置处理，提供完备的类型系统、语义化的编程接口，提高开发者的编码体验。😙

## 概念

###### 术语  解释  图示 

```
Base 多维表格文档
```
```
AppToken（又称
BaseId）
```
```
Base文档的唯一标识，可从BaseURL路径参数
/base/:app_token快速获得（图一）；但如果是/wiki/路
径，则不能便捷获得。
因此，我们建议直接通过【开发工具】插件快速获取当前Base的
AppToken（又称BaseId，⻅图二）。
```
```
PersonalBaseToken Base文档授权码。用戶针对某个Base文档生成的鉴权凭证，使用
凭证访问相应的接口可对Base数据进行读写。
```
```
注：使用PersonalBaseToken访问OpenAPI单文档限频2qps，多
文档支持并发。
( PersonalBaseToken使用指南)
```
## 安装

#### 本SDK支持Python3。

#### pip


```
pip install https://lf3-static.bytednsdoc.com/obj/eden-cn/lmeh7phbozvhoz/base-
open-sdk/baseopensdk-0.0.13-py3-none-any.whl
```
###### 1

#### poetry

```
poetry add https://lf3-static.bytednsdoc.com/obj/eden-cn/lmeh7phbozvhoz/base-
open-sdk/baseopensdk-0.0.13-py3-none-any.whl
```
###### 1

## 如何使用

#### SDK提供了语义化的调用方式，只需要提供相关参数创建client实例，接着使用其上的语义化方法

#### client.[业务域].[接口版本号].[资源].[方法]即可完成API调用。例如列出Base数据表记

#### 录：

##### from baseopensdk import BaseClient, JSON

##### from baseopensdk.api.base.v1 import *

##### from dotenv import load_dotenv, find_dotenv

##### import os

##### load_dotenv(find_dotenv())

##### APP_TOKEN = os.environ['APP_TOKEN']

##### PERSONAL_BASE_TOKEN = os.environ['PERSONAL_BASE_TOKEN']

##### TABLE_ID = os.environ['TABLE_ID']

##### # 构建client

```
client: BaseClient = BaseClient.builder() \
.app_token(APP_TOKEN) \
.personal_base_token(PERSONAL_BASE_TOKEN) \
.build()
```
##### # 构造请求对象

```
request = ListAppTableRecordRequest.builder() \
.table_id(TABLE_ID) \
.page_size( 20 ) \
.build()
```
##### # 发起请求

```
response = client.base.v1.app_table_record.list(request)
```
###### 1 2 3 4 5 6 7 8 9

###### 10

###### 11

###### 12

###### 13

###### 14

###### 15

###### 16

###### 17

###### 18

###### 19

###### 20

###### 21

###### 22

###### 23

###### 24

###### 25

###### 26


##### # 打印序列化数据

```
print(JSON.marshal(response.data, indent= 4 ))
```
###### 27

###### 28

### BaseClient构造参数：

###### 参数  描述  类型  必须  默认 

```
app_token Base文档的唯一标识，从Base网⻚的
路径参数获取/base/:app_token
```
```
str 是 -
```
```
personal_base_to
ken
```
```
Base文档授权码。从Base网⻚端获
取（如下图）
```
```
str 是 -
```
```
domain 域名 FEISHU_DOMAI
N/
LARK_DOMAIN
```
###### 否 FEISHU_DOMAIN

```
log_level 日志级别 LogLevel 否 LogLevel.INFO
```
### 使用海外L arkOpenAPI服务

#### domain默认为FEISHU_DOMAIN，可手动改为LARK_DOMAIN


##### from baseopensdk import BaseClient, LARK_DOMAIN

##### # 构建client

```
client: BaseClient = BaseClient.builder() \
.app_token(APP_TOKEN) \
.personal_base_token(PERSONAL_BASE_TOKEN) \
```
##### .domain(LARK_DOMAIN)

```
.build()
```
###### 1 2 3 4 5 6 7 8

### 附件上传

#### 和调用普通API的方式一样，按类型提示传递参数即可

```
from baseopensdk import BaseClient
from baseopensdk.api.drive.v1 import *
from dotenv import load_dotenv, find_dotenv
import os
```
```
load_dotenv(find_dotenv())
```
```
APP_TOKEN = os.environ['APP_TOKEN']
PERSONAL_BASE_TOKEN = os.environ['PERSONAL_BASE_TOKEN']
TABLE_ID = os.environ['TABLE_ID']
```
```
client = BaseClient.builder() \
.app_token(APP_TOKEN) \
.personal_base_token(PERSONAL_BASE_TOKEN) \
.build()
```
##### # 构造请求对象

```
file_name = 'test.txt'
path = os.path.abspath(file_name)
file = open(path, "rb")
request = UploadAllMediaRequest.builder() \
.request_body(UploadAllMediaRequestBody.builder()
.file_name(file_name)
.parent_type("bitable_file")
.parent_node(APP_TOKEN)
.size(os.path.getsize(path))
.file(file)
.build()) \
```
###### 1 2 3 4 5 6 7 8 9

###### 10

###### 11

###### 12

###### 13

###### 14

###### 15

###### 16

###### 17

###### 18

###### 19

###### 20

###### 21

###### 22

###### 23

###### 24

###### 25

###### 26

###### 27

###### 28

###### 29


```
.build()
```
##### # 发起请求

```
response: UploadAllMediaResponse = client.drive.v1.media.upload_all(request)
```
```
file_token = response.data.file_token
print(file_token)
```
###### 30

###### 31

###### 32

###### 33

###### 34

###### 35

###### 36

#### 上传附件后添加到新建记录的附件字段

##### # 构造请求对象

```
request = UpdateAppTableRecordRequest.builder() \
.table_id(TABLE_ID) \
.record_id(RECORD_ID) \
.request_body(AppTableRecord.builder()
.fields({
```
##### "附件": [{"file_token": file_token}] # 前面接口返回的

##### file_token

###### })

```
.build()) \
.build()
```
##### # 发起请求

```
response: UpdateAppTableRecordResponse =
client.base.v1.app_table_record.update(request)
```
###### 1 2 3 4 5 6 7 8 9

###### 10

###### 11

###### 12

###### 13

### 附件下载

```
from baseopensdk import BaseClient
from baseopensdk.api.drive.v1 import *
from dotenv import load_dotenv, find_dotenv
import os
import json
```
```
load_dotenv(find_dotenv())
```
```
APP_TOKEN = os.environ['APP_TOKEN']
PERSONAL_BASE_TOKEN = os.environ['PERSONAL_BASE_TOKEN']
TABLE_ID = os.environ['TABLE_ID']
```
###### 1 2 3 4 5 6 7 8 9

###### 10

###### 11

###### 12

###### 13


##### # 构建client

```
client = BaseClient.builder() \
.app_token(APP_TOKEN) \
.personal_base_token(PERSONAL_BASE_TOKEN) \
.build()
```
##### # 高级权限鉴权信息 文档未开启高级权限则无需传 extra 字段

```
extra = json.dumps({
"bitablePerm": {
```
##### "tableId": TABLE_ID, # 附件所在数据表 id

```
"attachments": {
```
##### FIELD_ID: { # 附件字段 id

##### RECORD_ID: [ # 附件所在记录 record_id

##### FILE_TOKEN # 附件 file_token

###### ]

###### }

###### }

###### }

###### })

##### # 构造请求对象

```
request = DownloadMediaRequest.builder() \
.file_token(FILE_TOKEN) \
.extra(extra) \
.build()
```
##### # 发起请求

```
response = client.drive.v1.media.download(request)
```
##### # 保存文件到本地

```
f = open(f"{response.file_name}", "wb")
f.write(response.file.read())
f.close()
```
###### 14

###### 15

###### 16

###### 17

###### 18

###### 19

###### 20

###### 21

###### 22

###### 23

###### 24

###### 25

###### 26

###### 27

###### 28

###### 29

###### 30

###### 31

###### 32

###### 33

###### 34

###### 35

###### 36

###### 37

###### 38

###### 39

###### 40

###### 41

###### 42

###### 43

###### 44

###### 45

###### 46

#### https://feishu.feishu.cn/sync/HmqHdmIXbswu4xbNd9gc7oqDnUe

## 完整示例

### 一、批量查找替换多行文本

```
from baseopensdk import BaseClient
from baseopensdk.api.base.v1 import *
from dotenv import load_dotenv, find_dotenv
```
###### 1

###### 2

###### 3


```
import os
```
```
load_dotenv(find_dotenv())
```
```
APP_TOKEN = os.environ['APP_TOKEN']
PERSONAL_BASE_TOKEN = os.environ['PERSONAL_BASE_TOKEN']
TABLE_ID = os.environ['TABLE_ID']
```
```
def search_and_replace(source: str, target: str):
```
##### # 1. 构建client

```
client: BaseClient = BaseClient.builder() \
.app_token(APP_TOKEN) \
.personal_base_token(PERSONAL_BASE_TOKEN) \
.build()
```
##### # 2. 获取当前表字段信息

```
list_field_request = ListAppTableFieldRequest.builder() \
.page_size( 100 ) \
.table_id(TABLE_ID) \
.build()
```
```
list_field_response =
client.base.v1.app_table_field.list(list_field_request)
fields = getattr(list_field_response.data, 'items', [])
```
##### # 3. 取出文本字段

```
text_field_names = [field.field_name for field in fields if field.ui_type
== 'Text']
```
##### # 4. 遍历记录

```
list_record_request = ListAppTableRecordRequest.builder() \
.page_size( 100 ) \
.table_id(TABLE_ID) \
.build()
```
```
list_record_response =
client.base.v1.app_table_record.list(list_record_request)
records = getattr(list_record_response.data, 'items', [])
```
```
records_need_update = []
```
```
for record in records:
record_id, fields = record.record_id, record.fields
new_fields = {}
```
```
for key, value in fields.items():
```
##### # 替换多行文本字段的值

###### 4 5 6 7 8 9

###### 10

###### 11

###### 12

###### 13

###### 14

###### 15

###### 16

###### 17

###### 18

###### 19

###### 20

###### 21

###### 22

###### 23

###### 24

###### 25

###### 26

###### 27

###### 28

###### 29

###### 30

###### 31

###### 32

###### 33

###### 34

###### 35

###### 36

###### 37

###### 38

###### 39

###### 40

###### 41

###### 42

###### 43

###### 44

###### 45

###### 46

###### 47


```
if key in text_field_names:
new_value = value.replace(source, target)
```
##### # 把需要替换的字段加入 new_fields

```
new_fields[key] = new_value if new_value != value else value
```
```
if len(new_fields.keys()) > 0 :
records_need_update.append({
"record_id": record_id,
"fields": new_fields
})
```
```
print(records_need_update)
```
##### # 5. 批量更新记录

```
batch_update_records_request = BatchUpdateAppTableRecordRequest().builder()
\
.table_id(TABLE_ID) \
.request_body(
BatchUpdateAppTableRecordRequestBody.builder() \
.records(records_need_update) \
.build()
) \
.build()
batch_update_records_response =
client.base.v1.app_table_record.batch_update(batch_update_records_request)
print('success!')
```
```
if __name__ == "__main__":
```
##### # 替换所有文本字段中 'abc' 为 '233333'

```
search_and_replace('abc', '233333')
```
###### 48

###### 49

###### 50

###### 51

###### 52

###### 53

###### 54

###### 55

###### 56

###### 57

###### 58

###### 59

###### 60

###### 61

###### 62

###### 63

###### 64

###### 65

###### 66

###### 67

###### 68

###### 69

###### 70

###### 71

###### 72

###### 73

###### 74

###### 75

###### 76

### 二、将链接字段对应的文件传到附件字段

```
from baseopensdk import BaseClient
from baseopensdk.api.base.v1 import *
from baseopensdk.api.drive.v1 import *
from dotenv import load_dotenv, find_dotenv
import os
import requests
```
```
load_dotenv(find_dotenv())
```
###### 1 2 3 4 5 6 7 8 9


```
APP_TOKEN = os.environ['APP_TOKEN']
PERSONAL_BASE_TOKEN = os.environ['PERSONAL_BASE_TOKEN']
TABLE_ID = os.environ['TABLE_ID']
```
```
def url_to_attachment():
```
##### # 1. 构建client

```
client: BaseClient = BaseClient.builder() \
.app_token(APP_TOKEN) \
.personal_base_token(PERSONAL_BASE_TOKEN) \
.build()
```
##### # 2. 遍历记录

```
list_record_request = ListAppTableRecordRequest.builder() \
.page_size( 100 ) \
.table_id(TABLE_ID) \
.build()
```
```
list_record_response =
client.base.v1.app_table_record.list(list_record_request)
records = getattr(list_record_response.data, 'items', [])
```
```
for record in records:
record_id, fields = record.record_id, record.fields
```
##### # 3. 拿到链接字段值

```
link = (fields.get('Link', {})).get('link')
if link:
```
##### # 4. 下载图片

```
image_resp = requests.get(link, stream=True)
content = image_resp.content
```
##### # 5. 上传图片到 Drive 获取 file_token

```
request = UploadAllMediaRequest.builder() \
.request_body(UploadAllMediaRequestBody.builder()
.file_name('test.png')
.parent_type("bitable_image")
.parent_node(APP_TOKEN)
.size(len(content))
.file(content)
.build()) \
.build()
response = client.drive.v1.media.upload_all(request)
```
```
file_token = response.data.file_token
print(file_token)
```
##### # 6. 更新 file_token 到附件字段

```
request = UpdateAppTableRecordRequest.builder() \
```
###### 10

###### 11

###### 12

###### 13

###### 14

###### 15

###### 16

###### 17

###### 18

###### 19

###### 20

###### 21

###### 22

###### 23

###### 24

###### 25

###### 26

###### 27

###### 28

###### 29

###### 30

###### 31

###### 32

###### 33

###### 34

###### 35

###### 36

###### 37

###### 38

###### 39

###### 40

###### 41

###### 42

###### 43

###### 44

###### 45

###### 46

###### 47

###### 48

###### 49

###### 50

###### 51

###### 52

###### 53

###### 54

###### 55


```
.table_id(TABLE_ID) \
.record_id(record_id) \
.request_body(AppTableRecord.builder()
.fields({
```
##### "Attachment": [{"file_token": file_token}] # 前面接口

##### 返回的 file_token

###### })

```
.build()) \
.build()
response: UpdateAppTableRecordResponse =
client.base.v1.app_table_record.update(request)
```
```
if __name__ == "__main__":
url_to_attachment()
```
###### 56

###### 57

###### 58

###### 59

###### 60

###### 61

###### 62

###### 63

###### 64

###### 65

###### 66

###### 67

###### 68

### 三、自动更新进度条

#### 自动更新进度条

## 在Replit上使用服务端SDK

#### 我们提供了一个Replit模板，它使用Flask框架搭建了一个简单的服务器，监听了指定路径，当我们

#### 在Base上运行这个脚本，就会触发脚本函数的调用。

```
from flask import Flask
from playground.search_and_replace import search_and_replace_func
```
```
app = Flask(__name__)
```
```
@app.route('/')
def index():
return 'Hello from Flask!'
```
```
@app.route('/search_and_replace')
def search_and_replace():
search_and_replace_func('abc', '123')
return 'success！！！'
```
```
app.run(host='0.0.0.0', port= 81 )
```
###### 1 2 3 4 5 6 7 8 9

###### 10

###### 11

###### 12

###### 13

###### 14

###### 15

###### 16

###### 17


#### 上述代码监听/search_and_replace接口路径，并执我们的示例一中定义的函数，实现操作

#### Base数据

### 方式一：在B aseS cript使用Replit链接触发脚本调用

#### 1. 在Replit上Fork官方模板

#### 2. 通过ReplitSecret添加环境变量APP_TOKEN、PERSONAL_BASE_TOKEN、TABLE_ID

#### 3. 点击Run起Replit服务

#### 4. 拷⻉replit项目域名+接口路径，填入BaseScript，保存后点击运行即可触发服务端脚本

### 方式二：Replit服务端直接运行脚本

#### 如果你的项目无需手动触发，可以直接在Replit控制台运行脚本

```
1 python ./playground/search_and_replace.py
```

