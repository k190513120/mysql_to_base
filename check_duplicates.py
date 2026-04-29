#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描飞书多维表格中按 MySQL 主键分组的重复记录情况。

只读，不做任何修改。输出：
  table_name | pk | base_records | unique_pks | dup_groups | dup_extra_records
"""

import os
import sys
import time
from collections import defaultdict
from typing import Dict, List, Optional

import pymysql
from dotenv import load_dotenv
from baseopensdk import BaseClient, FEISHU_DOMAIN, LARK_DOMAIN
from baseopensdk.api.base.v1 import (
    ListAppTableRequest,
    ListAppTableRecordRequest,
)


def list_base_tables(client) -> Dict[str, str]:
    resp = client.base.v1.app_table.list(ListAppTableRequest.builder().build())
    if not resp.success():
        raise RuntimeError(f"list tables failed: {resp.msg}")
    return {t.name: t.table_id for t in resp.data.items}


def list_records(client, table_id: str) -> List:
    """完整分页拉取（带简单重试，不容忍残缺）。"""
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


def get_mysql_primary_key(conn, db: str, table: str) -> Optional[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND CONSTRAINT_NAME='PRIMARY'
            ORDER BY ORDINAL_POSITION LIMIT 1
            """,
            (db, table),
        )
        row = cur.fetchone()
        return row[0] if row else None


def main():
    load_dotenv()
    mysql_host = os.environ['MYSQL_HOST']
    mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
    mysql_user = os.environ['MYSQL_USERNAME']
    mysql_pwd = os.environ['MYSQL_PASSWORD']
    mysql_db = os.environ['MYSQL_DATABASE']
    app_token = os.environ['APP_TOKEN']
    pbt = os.environ['PERSONAL_BASE_TOKEN']
    region = os.environ.get('REGION', 'domestic')

    domain = LARK_DOMAIN if region == 'overseas' else FEISHU_DOMAIN
    client = BaseClient.builder().app_token(app_token).personal_base_token(pbt).domain(domain).build()

    conn = pymysql.connect(
        host=mysql_host, port=mysql_port, user=mysql_user, password=mysql_pwd,
        database=mysql_db, charset='utf8mb4',
    )

    base_tables = list_base_tables(client)
    print(f"飞书表数量: {len(base_tables)}")

    print(f"\n{'table':<40} {'pk':<14} {'base_recs':>10} {'unique_pk':>10} {'dup_grps':>9} {'dup_extra':>10}")
    print('-' * 100)

    grand_dup_extra = 0
    affected = []

    for table_name in sorted(base_tables):
        table_id = base_tables[table_name]
        pk = get_mysql_primary_key(conn, mysql_db, table_name)
        if not pk:
            print(f"{table_name:<40} {'(no pk)':<14}  -- 跳过")
            continue

        try:
            records = list_records(client, table_id)
        except Exception as e:
            print(f"{table_name:<40} {pk:<14}  -- 列出失败: {e}")
            continue

        groups: Dict[str, List[str]] = defaultdict(list)
        no_pk = 0
        for r in records:
            if pk in r.fields:
                key = str(r.fields[pk])
                groups[key].append(r.record_id)
            else:
                no_pk += 1

        unique_pks = len(groups)
        dup_grps = sum(1 for ids in groups.values() if len(ids) > 1)
        dup_extra = sum(len(ids) - 1 for ids in groups.values() if len(ids) > 1)
        grand_dup_extra += dup_extra

        flag = '  ⚠' if dup_extra > 0 else ''
        print(f"{table_name:<40} {pk:<14} {len(records):>10} {unique_pks:>10} {dup_grps:>9} {dup_extra:>10}{flag}")

        if dup_extra > 0:
            affected.append((table_name, table_id, pk, dup_extra))

    print('-' * 100)
    print(f"\n总计需要清理的重复记录: {grand_dup_extra} 条，涉及 {len(affected)} 张表")
    if affected:
        print("\n受影响的表:")
        for t, _, pk, n in affected:
            print(f"  {t} (pk={pk}, 多余={n})")

    conn.close()


if __name__ == '__main__':
    main()
