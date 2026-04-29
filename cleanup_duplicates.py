#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理飞书多维表格中按 MySQL 主键（含复合主键）分组的重复记录。

策略：
  1. 从 MySQL 读取每张表的完整 PRIMARY KEY 列序列。
  2. 拉取飞书表全部记录，按主键值元组分组。
  3. 每个组内保留 record_id 字典序最小的一条（创建时间最早），其余删除。
  4. 主键任一列在飞书侧缺失/为空 → 跳过该组（不动）。
  5. 仅删除"真正的重复"，绝不动单条记录组。

调用：
  python3 cleanup_duplicates.py            # 仅打印计划，不执行
  python3 cleanup_duplicates.py --execute  # 真正执行删除
"""

import os
import sys
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import pymysql
from dotenv import load_dotenv
from baseopensdk import BaseClient, FEISHU_DOMAIN, LARK_DOMAIN
from baseopensdk.api.base.v1 import (
    ListAppTableRequest,
    ListAppTableRecordRequest,
    BatchDeleteAppTableRecordRequest,
    BatchDeleteAppTableRecordRequestBody,
)


def list_base_tables(client) -> Dict[str, str]:
    resp = client.base.v1.app_table.list(ListAppTableRequest.builder().build())
    if not resp.success():
        raise RuntimeError(f"list tables failed: {resp.msg}")
    return {t.name: t.table_id for t in resp.data.items}


def list_records(client, table_id: str) -> List:
    out = []
    page_token = None
    while True:
        for attempt in range(5):
            builder = ListAppTableRecordRequest.builder().table_id(table_id).page_size(500)
            if page_token:
                builder.page_token(page_token)
            resp = client.base.v1.app_table_record.list(builder.build())
            if resp.success():
                break
            wait = 2 ** attempt
            print(f"  [warn] list page failed: {resp.msg}, retry in {wait}s", flush=True)
            time.sleep(wait)
        else:
            raise RuntimeError(f"列出 {table_id} 失败: {resp.msg}")

        if resp.data and resp.data.items:
            out.extend(resp.data.items)
        if getattr(resp.data, 'has_more', False):
            page_token = resp.data.page_token
            time.sleep(0.2)
        else:
            break
    return out


def get_mysql_pk_cols(conn, db: str, table: str) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND CONSTRAINT_NAME='PRIMARY'
            ORDER BY ORDINAL_POSITION
            """,
            (db, table),
        )
        return [r[0] for r in cur.fetchall()]


def batch_delete(client, table_id: str, record_ids: List[str]) -> int:
    """分批删除，返回成功删除数量。带瞬时错误指数退避重试。"""
    deleted = 0
    BATCH = 500
    for i in range(0, len(record_ids), BATCH):
        chunk = record_ids[i:i + BATCH]
        for attempt in range(5):
            req = BatchDeleteAppTableRecordRequest.builder() \
                .table_id(table_id) \
                .request_body(
                    BatchDeleteAppTableRecordRequestBody.builder()
                    .records(chunk)
                    .build()
                ) \
                .build()
            resp = client.base.v1.app_table_record.batch_delete(req)
            if resp.success():
                deleted += len(chunk)
                break
            wait = 2 ** attempt
            print(f"    [warn] batch_delete failed: {resp.msg}, retry in {wait}s", flush=True)
            time.sleep(wait)
        else:
            raise RuntimeError(f"批量删除失败: {resp.msg}")
        time.sleep(0.3)
    return deleted


def main():
    execute = '--execute' in sys.argv

    load_dotenv('/Users/lan/Desktop/mysql同步项目/repo/.env')
    mysql_host = os.environ['MYSQL_HOST']
    mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
    mysql_user = os.environ['MYSQL_USERNAME']
    mysql_pwd = os.environ['MYSQL_PASSWORD']
    mysql_db = os.environ['MYSQL_DATABASE']
    app_token = os.environ['APP_TOKEN']
    pbt = os.environ['PERSONAL_BASE_TOKEN']
    region = os.environ.get('REGION', 'domestic')

    mode = '执行删除' if execute else 'DRY-RUN（仅打印计划）'
    print(f"=== 清理模式: {mode} ===\n")

    domain = LARK_DOMAIN if region == 'overseas' else FEISHU_DOMAIN
    client = BaseClient.builder().app_token(app_token).personal_base_token(pbt).domain(domain).build()
    conn = pymysql.connect(
        host=mysql_host, port=mysql_port, user=mysql_user, password=mysql_pwd,
        database=mysql_db, charset='utf8mb4',
    )

    base_tables = list_base_tables(client)
    print(f"飞书表数量: {len(base_tables)}\n")

    grand_planned = 0
    grand_deleted = 0

    for table_name in sorted(base_tables):
        table_id = base_tables[table_name]
        pk_cols = get_mysql_pk_cols(conn, mysql_db, table_name)
        if not pk_cols:
            continue

        try:
            records = list_records(client, table_id)
        except Exception as e:
            print(f"[{table_name}] 列出失败: {e}，跳过")
            continue

        if not records:
            continue

        # 按 PK 元组分组
        groups: Dict[Tuple, List[str]] = defaultdict(list)
        skipped_no_pk = 0
        for r in records:
            try:
                key = tuple(str(r.fields[c]) for c in pk_cols)
            except KeyError:
                skipped_no_pk += 1
                continue
            groups[key].append(r.record_id)

        # 找出多余记录（每组保留 record_id 字典序最小的一条）
        to_delete: List[str] = []
        for key, ids in groups.items():
            if len(ids) <= 1:
                continue
            ids_sorted = sorted(ids)
            to_delete.extend(ids_sorted[1:])

        if not to_delete:
            continue

        pk_repr = '+'.join(pk_cols)
        print(f"[{table_name}] pk={pk_repr}  记录={len(records)}  唯一组={len(groups)}  待删除={len(to_delete)}"
              + (f"  (跳过缺主键={skipped_no_pk})" if skipped_no_pk else ''))
        grand_planned += len(to_delete)

        if execute:
            try:
                n = batch_delete(client, table_id, to_delete)
                grand_deleted += n
                print(f"    ✓ 删除完成 {n} 条")
            except Exception as e:
                print(f"    ✗ 删除失败: {e}")

    print(f"\n=== 汇总 ===")
    print(f"计划删除: {grand_planned} 条")
    if execute:
        print(f"实际删除: {grand_deleted} 条")
    else:
        print("(DRY-RUN，未执行删除；加 --execute 真正执行)")

    conn.close()


if __name__ == '__main__':
    main()
