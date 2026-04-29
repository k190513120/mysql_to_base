#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL到飞书多维表格同步脚本
实现MySQL数据库表数据同步到飞书多维表格的功能
"""

import os
import sys
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time

import pymysql
from baseopensdk import BaseClient, LARK_DOMAIN, FEISHU_DOMAIN
from baseopensdk.api.base.v1 import *


@dataclass
class MySQLConfig:
    """MySQL数据库配置"""
    host: str
    port: int
    username: str
    password: str
    database: str


@dataclass
class BaseConfig:
    """飞书多维表格配置"""
    app_token: str
    personal_base_token: str
    region: str = 'domestic'  # 'domestic' for 国内飞书, 'overseas' for 海外Lark


class DataTypeMapper:
    """数据类型映射器"""
    
    # MySQL到飞书多维表格字段类型映射
    TYPE_MAPPING = {
        # 数值类型
        'tinyint': 'Number',
        'smallint': 'Number', 
        'mediumint': 'Number',
        'int': 'Number',
        'integer': 'Number',
        'bigint': 'Number',
        'float': 'Number',
        'double': 'Number',
        'decimal': 'Number',
        'numeric': 'Number',
        
        # 字符串类型
        'char': 'Text',
        'varchar': 'Text',
        'tinytext': 'Text',
        'text': 'Text',
        'mediumtext': 'Text',
        'longtext': 'Text',
        
        # 日期时间类型
        'date': 'DateTime',
        'time': 'DateTime',
        'datetime': 'DateTime',
        'timestamp': 'DateTime',
        'year': 'Number',
        
        # 二进制类型
        'binary': 'Text',
        'varbinary': 'Text',
        'tinyblob': 'Attachment',
        'blob': 'Attachment',
        'mediumblob': 'Attachment',
        'longblob': 'Attachment',
        
        # JSON类型
        'json': 'Text',
        
        # 枚举类型
        'enum': 'SingleSelect',
        'set': 'MultiSelect',
        
        # 布尔类型
        'boolean': 'Checkbox',
        'bool': 'Checkbox',
    }
    
    @classmethod
    def get_base_field_type(cls, mysql_type: str) -> str:
        """获取飞书多维表格字段类型"""
        # 提取基础类型名（去除长度限制等）
        base_type = mysql_type.lower().split('(')[0].strip()
        return cls.TYPE_MAPPING.get(base_type, 'Text')
    
    @classmethod
    def convert_value(cls, value: Any, mysql_type: str) -> Any:
        """转换数据值"""
        if value is None:
            return None
            
        base_type = mysql_type.lower().split('(')[0].strip()
        
        # 日期时间类型转换
        if base_type in ['date', 'datetime', 'timestamp']:
            if isinstance(value, (datetime,)):
                return int(value.timestamp() * 1000)  # 转换为毫秒时间戳
            elif isinstance(value, str):
                try:
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    return int(dt.timestamp() * 1000)
                except:
                    return value
        
        # 布尔类型转换
        elif base_type in ['boolean', 'bool']:
            return bool(value)
        
        # 数值类型转换
        elif base_type in ['tinyint', 'smallint', 'mediumint', 'int', 'integer', 'bigint']:
            return int(value) if value is not None else None
        elif base_type in ['float', 'double', 'decimal', 'numeric']:
            return float(value) if value is not None else None
        
        # 其他类型转为字符串
        else:
            return str(value) if value is not None else None


# 飞书 Base 的瞬时错误关键词（出现这些就重试）
_TRANSIENT_MSG_KEYWORDS = (
    'data not ready',
    'try again',
    'timeout',
    'rate limit',
    'too many request',
    'service unavailable',
    'internal error',
)


def _is_transient_error(response) -> bool:
    """判断飞书 API 响应是否是可重试的瞬时错误"""
    msg = (getattr(response, 'msg', '') or '').lower()
    if any(kw in msg for kw in _TRANSIENT_MSG_KEYWORDS):
        return True
    # 已知的瞬时错误码
    code = getattr(response, 'code', None)
    return code in (1254290, 1254607, 91402, 99991400, 99991663, 99991672)


class MySQLToBaseSync:
    """MySQL到飞书多维表格同步器"""

    def __init__(self, mysql_config: MySQLConfig, base_config: BaseConfig):
        self.mysql_config = mysql_config
        self.base_config = base_config
        self.mysql_conn = None
        self.base_client = None
        self.logger = self._setup_logger()

    def _call_with_retry(self, op_name: str, fn, max_retries: int = 5):
        """对一次飞书 API 调用做指数退避重试。

        - 成功（response.success() == True）→ 返回 response
        - 瞬时错误（_is_transient_error）→ 退避重试
        - 非瞬时错误或重试用尽 → 抛 RuntimeError
        - 调用本身抛异常 → 同样退避重试，最后一次仍抛则向上抛
        """
        last_err = None
        for attempt in range(max_retries):
            try:
                response = fn()
                if response.success():
                    return response
                if _is_transient_error(response) and attempt < max_retries - 1:
                    wait = 2 ** attempt
                    self.logger.warning(
                        f"{op_name} 瞬时错误 [code={getattr(response, 'code', None)}] "
                        f"{getattr(response, 'msg', '')}，{wait}s 后第 {attempt + 2}/{max_retries} 次重试"
                    )
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    f"{op_name} 失败: code={getattr(response, 'code', None)} "
                    f"msg={getattr(response, 'msg', '')}"
                )
            except RuntimeError:
                raise
            except Exception as e:
                last_err = e
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    self.logger.warning(
                        f"{op_name} 调用异常: {e}，{wait}s 后第 {attempt + 2}/{max_retries} 次重试"
                    )
                    time.sleep(wait)
                    continue
                raise
        raise RuntimeError(f"{op_name} 重试 {max_retries} 次仍失败: {last_err}")
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('mysql_to_base_sync')
        logger.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler('sync.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def connect_mysql(self) -> bool:
        """连接MySQL数据库"""
        try:
            self.mysql_conn = pymysql.connect(
                host=self.mysql_config.host,
                port=self.mysql_config.port,
                user=self.mysql_config.username,
                password=self.mysql_config.password,
                database=self.mysql_config.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.logger.info(f"成功连接到MySQL数据库: {self.mysql_config.host}:{self.mysql_config.port}")
            return True
        except Exception as e:
            self.logger.error(f"连接MySQL数据库失败: {e}")
            return False
    
    def connect_base(self) -> bool:
        """连接飞书多维表格"""
        try:
            # 根据区域选择domain
            domain = LARK_DOMAIN if self.base_config.region == 'overseas' else FEISHU_DOMAIN
            
            self.base_client = BaseClient.builder() \
                .app_token(self.base_config.app_token) \
                .personal_base_token(self.base_config.personal_base_token) \
                .domain(domain) \
                .build()
            
            region_name = "海外Lark" if self.base_config.region == 'overseas' else "国内飞书"
            self.logger.info(f"成功连接到{region_name}多维表格")
            return True
        except Exception as e:
            self.logger.error(f"连接飞书多维表格失败: {e}")
            return False
    
    def get_mysql_tables(self) -> List[str]:
        """获取MySQL数据库中的所有表"""
        try:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [row[f'Tables_in_{self.mysql_config.database}'] for row in cursor.fetchall()]
                self.logger.info(f"发现 {len(tables)} 个MySQL表: {tables}")
                return tables
        except Exception as e:
            self.logger.error(f"获取MySQL表列表失败: {e}")
            return []
    
    def get_table_schema(self, table_name: str) -> List[Dict]:
        """获取MySQL表结构"""
        try:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = cursor.fetchall()
                
                schema = []
                for col in columns:
                    field_info = {
                        'name': col['Field'],
                        'type': col['Type'],
                        'null': col['Null'] == 'YES',
                        'key': col['Key'],
                        'default': col['Default'],
                        'extra': col['Extra']
                    }
                    schema.append(field_info)
                
                self.logger.info(f"获取表 {table_name} 结构，共 {len(schema)} 个字段")
                return schema
        except Exception as e:
            self.logger.error(f"获取表 {table_name} 结构失败: {e}")
            return []
    
    def create_base_table(self, table_name: str, schema: List[Dict]) -> Optional[str]:
        """在飞书多维表格中创建表"""
        try:
            # 构建字段定义 - 使用正确的AppTableCreateHeader.builder()格式
            fields = []
            for col in schema:
                field_type = DataTypeMapper.get_base_field_type(col['type'])
                type_mapping = {
                    'Text': 1,
                    'Number': 2, 
                    'SingleSelect': 3,
                    'MultiSelect': 4,
                    'DateTime': 5,
                    'Checkbox': 7,
                    'Attachment': 11
                }
                
                field_builder = AppTableCreateHeader.builder() \
                    .field_name(col['name']) \
                    .type(type_mapping.get(field_type, 1))  # 默认为文本类型
                
                # 添加ui_type（可选）
                if field_type in ['SingleSelect', 'MultiSelect', 'DateTime', 'Checkbox', 'Attachment']:
                    field_builder.ui_type(field_type)
                
                # 为单选和多选字段添加选项
                if field_type == 'SingleSelect':
                    property_builder = AppTableFieldProperty.builder() \
                        .options([
                            AppTableFieldPropertyOption.builder()
                                .name('选项1')
                                .color(1)
                                .build(),
                            AppTableFieldPropertyOption.builder()
                                .name('选项2')
                                .color(2)
                                .build(),
                            AppTableFieldPropertyOption.builder()
                                .name('选项3')
                                .color(3)
                                .build()
                        ])
                    field_builder.property(property_builder.build())
                elif field_type == 'MultiSelect':
                    property_builder = AppTableFieldProperty.builder() \
                        .options([
                            AppTableFieldPropertyOption.builder()
                                .name('选项1')
                                .color(1)
                                .build(),
                            AppTableFieldPropertyOption.builder()
                                .name('选项2')
                                .color(2)
                                .build(),
                            AppTableFieldPropertyOption.builder()
                                .name('选项3')
                                .color(3)
                                .build()
                        ])
                    field_builder.property(property_builder.build())
                
                fields.append(field_builder.build())
            
            # 创建表请求
            request = CreateAppTableRequest.builder() \
                .request_body(
                    CreateAppTableRequestBody.builder()
                    .table(
                        ReqTable.builder()
                        .name(table_name)
                        .default_view_name("默认视图")
                        .fields(fields)
                        .build()
                    )
                    .build()
                ) \
                .build()
            
            response = self.base_client.base.v1.app_table.create(request)
            
            if response.success():
                table_id = response.data.table_id
                self.logger.info(f"成功创建飞书表格: {table_name} (ID: {table_id})")
                return table_id
            else:
                self.logger.error(f"创建飞书表格失败: {response.msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"创建飞书表格 {table_name} 失败: {e}")
            return None
    
    def get_base_tables(self) -> Dict[str, str]:
        """获取飞书多维表格中的所有表"""
        try:
            request = ListAppTableRequest.builder().build()
            response = self.base_client.base.v1.app_table.list(request)
            
            if response.success():
                tables = {}
                for table in response.data.items:
                    tables[table.name] = table.table_id
                self.logger.info(f"发现 {len(tables)} 个飞书表格")
                return tables
            else:
                self.logger.error(f"获取飞书表格列表失败: {response.msg}")
                return {}
        except Exception as e:
            self.logger.error(f"获取飞书表格列表失败: {e}")
            return {}
    
    def get_mysql_data(self, table_name: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """获取MySQL表数据"""
        try:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {limit} OFFSET {offset}")
                data = cursor.fetchall()
                self.logger.info(f"从表 {table_name} 获取 {len(data)} 条记录")
                return data
        except Exception as e:
            self.logger.error(f"获取表 {table_name} 数据失败: {e}")
            return []
    
    def get_primary_key(self, table_name: str) -> List[str]:
        """获取表的完整主键字段列表（按列序）。

        返回值是按 ORDINAL_POSITION 排序的列名列表：
          - 单列主键：['id']
          - 复合主键：['admin_id', 'role_id']
          - 无主键：  []
        """
        try:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_NAME = %s
                      AND CONSTRAINT_NAME = 'PRIMARY'
                    ORDER BY ORDINAL_POSITION
                    """,
                    (self.mysql_config.database, table_name),
                )
                rows = cursor.fetchall()
                return [r['COLUMN_NAME'] for r in rows] if rows else []
        except Exception as e:
            self.logger.error(f"获取表 {table_name} 主键失败: {e}")
            return []

    @staticmethod
    def _make_pk_key(fields: Dict[str, Any], pk_cols: List[str]) -> Optional[str]:
        """从 fields 中按主键列序取值，构建组合去重 key。

        任一主键列缺失或值为 None → 返回 None（调用方应回退到全字段哈希）。
        多列时用 '\x1f'（unit separator，避免与正常文本碰撞）拼接。
        """
        parts = []
        for c in pk_cols:
            if c not in fields or fields[c] is None:
                return None
            parts.append(str(fields[c]))
        return '\x1f'.join(parts)

    def get_existing_records(
        self, table_id: str, primary_key: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """获取飞书表格中已存在的记录，基于（可能复合的）主键建立映射。

        任何分页失败都会抛异常 —— 调用方必须捕获并中止该表同步，
        绝不能拿残缺/空的去重表去做写入（否则会全表当作新记录批量插入造成重复）。
        """
        pk_cols = list(primary_key) if primary_key else []
        existing_records: Dict[str, str] = {}
        page_token = None
        skipped_no_pk = 0

        while True:
            def _do_list(_pt=page_token):
                builder = ListAppTableRecordRequest.builder() \
                    .table_id(table_id) \
                    .page_size(500)
                if _pt:
                    builder.page_token(_pt)
                return self.base_client.base.v1.app_table_record.list(builder.build())

            response = self._call_with_retry(f"列出表 {table_id} 已存在记录", _do_list)

            if hasattr(response.data, 'items') and response.data.items:
                for record in response.data.items:
                    record_key = None
                    if pk_cols:
                        record_key = self._make_pk_key(record.fields, pk_cols)
                    if record_key is None:
                        # 没有主键、或飞书侧主键列缺失 → 回退到全字段哈希
                        if pk_cols:
                            skipped_no_pk += 1
                        field_values = []
                        for key, value in record.fields.items():
                            field_values.append(f"{key}:{value}")
                        record_key = hashlib.md5(
                            '|'.join(sorted(field_values)).encode()
                        ).hexdigest()
                    existing_records[record_key] = record.record_id

            if hasattr(response.data, 'has_more') and response.data.has_more:
                page_token = response.data.page_token
                time.sleep(0.2)
            else:
                break

        if pk_cols:
            extra = f"，{skipped_no_pk} 条主键缺失回退哈希" if skipped_no_pk else ''
            self.logger.info(
                f"获取到 {len(existing_records)} 条已存在记录（基于主键 {'+'.join(pk_cols)}{extra}）"
            )
        else:
            self.logger.info(f"获取到 {len(existing_records)} 条已存在记录（基于全字段哈希）")
        return existing_records
    
    def sync_table_data(self, mysql_table: str, base_table_id: str, schema: List[Dict], incremental: bool = True) -> bool:
        """同步表数据（支持增量同步）"""
        try:
            # 获取主键字段（可能是复合主键）
            pk_cols = self.get_primary_key(mysql_table)
            if pk_cols:
                self.logger.info(f"表 {mysql_table} 主键: {'+'.join(pk_cols)}")
            else:
                self.logger.info(f"表 {mysql_table} 无主键，将使用全字段哈希去重")

            # 获取已存在的记录（用于去重和更新）
            existing_records = {}
            if incremental:
                try:
                    existing_records = self.get_existing_records(base_table_id, pk_cols)
                except Exception as e:
                    # 拿不到完整去重表 → 中止该表同步，避免把所有 MySQL 行当新记录批量插入造成重复
                    self.logger.error(
                        f"表 {mysql_table} 获取已存在记录失败，跳过本次同步以避免重复写入: {e}"
                    )
                    return False
            
            # 分批获取数据
            batch_size = 500
            offset = 0
            total_synced = 0
            total_updated = 0
            total_created = 0
            
            while True:
                # 获取MySQL数据
                mysql_data = self.get_mysql_data(mysql_table, batch_size, offset)
                if not mysql_data:
                    break
                
                # 转换数据格式并处理增量同步
                new_records = []
                update_records = []
                
                for row in mysql_data:
                    fields = {}
                    for col in schema:
                        col_name = col['name']
                        if col_name in row:
                            value = DataTypeMapper.convert_value(row[col_name], col['type'])
                            if value is not None:
                                fields[col_name] = value
                    
                    if not fields:  # 跳过空记录
                        continue
                    
                    # 生成记录唯一标识：组合主键所有列拼出元组 key
                    record_key = self._make_pk_key(fields, pk_cols) if pk_cols else None
                    if record_key is None:
                        # 无主键 / 主键列缺失 → 回退到全字段哈希（与读取侧逻辑保持一致）
                        field_values = []
                        for key, value in fields.items():
                            field_values.append(f"{key}:{value}")
                        record_key = hashlib.md5('|'.join(sorted(field_values)).encode()).hexdigest()

                    # 检查记录是否已存在
                    if incremental and record_key in existing_records:
                        # 记录已存在，准备更新
                        update_records.append({
                            'record_id': existing_records[record_key],
                            'fields': fields
                        })
                        if pk_cols:
                            self.logger.debug(f"准备更新记录，主键 {'+'.join(pk_cols)}={record_key}")
                    else:
                        # 新记录，准备创建
                        new_records.append({'fields': fields})
                        if pk_cols:
                            self.logger.debug(f"准备创建新记录，主键 {'+'.join(pk_cols)}={record_key}")
                
                # 批量创建新记录
                if new_records:
                    success = self._batch_create_records(base_table_id, new_records)
                    if success:
                        total_created += len(new_records)
                        self.logger.info(f"成功创建 {len(new_records)} 条新记录")
                    else:
                        self.logger.error(f"创建新记录失败")
                        return False
                
                # 批量更新已存在记录
                if update_records:
                    success = self._batch_update_records(base_table_id, update_records)
                    if success:
                        total_updated += len(update_records)
                        self.logger.info(f"成功更新 {len(update_records)} 条记录")
                    else:
                        self.logger.error(f"更新记录失败")
                        return False
                
                total_synced += len(new_records) + len(update_records)
                offset += batch_size
                
                # 添加延迟避免频率限制
                time.sleep(0.5)
            
            self.logger.info(f"表 {mysql_table} 同步完成 - 总计: {total_synced}, 新增: {total_created}, 更新: {total_updated}")
            return True
            
        except Exception as e:
            self.logger.error(f"同步表 {mysql_table} 数据失败: {e}")
            return False
    
    def _batch_update_records(self, table_id: str, records: List[Dict]) -> bool:
        """批量更新记录（带瞬时错误重试）"""
        try:
            max_batch_size = 500  # 飞书 API 限制每次最多 500 条

            for i in range(0, len(records), max_batch_size):
                batch_records = records[i:i + max_batch_size]

                def _do_update(_batch=batch_records):
                    request = BatchUpdateAppTableRecordRequest.builder() \
                        .table_id(table_id) \
                        .request_body(
                            BatchUpdateAppTableRecordRequestBody.builder()
                            .records(_batch)
                            .build()
                        ) \
                        .build()
                    return self.base_client.base.v1.app_table_record.batch_update(request)

                self._call_with_retry(f"批量更新表 {table_id} 记录", _do_update)
                time.sleep(0.5)

            return True

        except Exception as e:
            self.logger.error(f"批量更新记录失败: {e}")
            return False

    def _batch_create_records(self, table_id: str, records: List[Dict]) -> bool:
        """批量创建记录（带瞬时错误重试）"""
        try:
            max_batch_size = 500

            for i in range(0, len(records), max_batch_size):
                batch_records = records[i:i + max_batch_size]

                def _do_create(_batch=batch_records):
                    request = BatchCreateAppTableRecordRequest.builder() \
                        .table_id(table_id) \
                        .request_body(
                            BatchCreateAppTableRecordRequestBody.builder()
                            .records(_batch)
                            .build()
                        ) \
                        .build()
                    return self.base_client.base.v1.app_table_record.batch_create(request)

                self._call_with_retry(f"批量创建表 {table_id} 记录", _do_create)
                time.sleep(0.5)

            return True

        except Exception as e:
            self.logger.error(f"批量创建记录失败: {e}")
            return False
    
    def sync_all_tables(self) -> Dict[str, bool]:
        """同步所有表"""
        results = {}
        
        try:
            # 获取MySQL表列表
            mysql_tables = self.get_mysql_tables()
            if not mysql_tables:
                self.logger.error("未找到MySQL表")
                return results
            
            # 获取现有的飞书表格
            base_tables = self.get_base_tables()
            
            for table_name in mysql_tables:
                self.logger.info(f"开始同步表: {table_name}")
                
                try:
                    # 获取表结构
                    schema = self.get_table_schema(table_name)
                    if not schema:
                        results[table_name] = False
                        continue
                    
                    # 检查飞书表格是否存在，不存在则创建
                    table_id = base_tables.get(table_name)
                    if not table_id:
                        table_id = self.create_base_table(table_name, schema)
                        if not table_id:
                            results[table_name] = False
                            continue
                    else:
                        self.logger.info(f"表 {table_name} 已存在，跳过创建")
                    
                    # 同步数据
                    success = self.sync_table_data(table_name, table_id, schema)
                    results[table_name] = success
                    
                except Exception as e:
                    self.logger.error(f"同步表 {table_name} 失败: {e}")
                    results[table_name] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"同步所有表失败: {e}")
            return results
    
    def close_connections(self):
        """关闭连接"""
        if self.mysql_conn:
            self.mysql_conn.close()
            self.logger.info("MySQL连接已关闭")


def sync_with_config(mysql_host: str, mysql_port: int, mysql_username: str, 
                     mysql_password: str, mysql_database: str, 
                     app_token: str, personal_base_token: str, 
                     region: str = 'domestic') -> Dict[str, bool]:
    """使用指定配置进行同步"""
    mysql_config = MySQLConfig(
        host=mysql_host,
        port=mysql_port,
        username=mysql_username,
        password=mysql_password,
        database=mysql_database
    )
    
    base_config = BaseConfig(
        app_token=app_token,
        personal_base_token=personal_base_token,
        region=region
    )
    
    # 创建同步器
    syncer = MySQLToBaseSync(mysql_config, base_config)
    
    try:
        # 连接数据库
        if not syncer.connect_mysql():
            raise Exception("MySQL连接失败")
        
        if not syncer.connect_base():
            raise Exception("飞书多维表格连接失败")
        
        # 开始同步
        results = syncer.sync_all_tables()
        return results
        
    except Exception as e:
        syncer.logger.error(f"同步失败: {e}")
        raise e
    finally:
        syncer.close_connections()


def main():
    """主函数"""
    print("=" * 60)
    print("MySQL到飞书多维表格同步工具")
    print("=" * 60)
    
    # 获取用户输入或使用默认配置
    mysql_config = MySQLConfig(
        host="rm-zf81e68a31gsqv1c7zo.mysql.kualalumpur.rds.aliyuncs.com",
        port=3306,
        username="writer_readonly",
        password="c*xZ%BEu2VikL%G",
        database=input("请输入MySQL数据库名: ").strip()
    )
    
    base_config = BaseConfig(
        app_token=input("请输入飞书多维表格APP_TOKEN: ").strip(),
        personal_base_token=input("请输入飞书多维表格PERSONAL_BASE_TOKEN: ").strip()
    )
    
    # 创建同步器
    syncer = MySQLToBaseSync(mysql_config, base_config)
    
    try:
        # 连接数据库
        print("\n正在连接数据库...")
        if not syncer.connect_mysql():
            print("MySQL连接失败，程序退出")
            return
        
        if not syncer.connect_base():
            print("飞书多维表格连接失败，程序退出")
            return
        
        print("数据库连接成功！")
        
        # 开始同步
        print("\n开始同步数据...")
        results = syncer.sync_all_tables()
        
        # 显示结果
        print("\n" + "=" * 60)
        print("同步结果统计:")
        print("=" * 60)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        for table_name, success in results.items():
            status = "✓ 成功" if success else "✗ 失败"
            print(f"{table_name}: {status}")
        
        print(f"\n总计: {success_count}/{total_count} 个表同步成功")
        
        if success_count == total_count:
            print("🎉 所有表同步完成！")
        else:
            print("⚠️  部分表同步失败，请查看日志文件 sync.log")
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
    finally:
        syncer.close_connections()


if __name__ == "__main__":
    main()