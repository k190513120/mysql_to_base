#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口文件
用于接收HTTP请求并启动MySQL到飞书多维表格的同步任务
"""

import json
import os
import sys
from typing import Dict, Any
from mysql_to_base_sync import sync_with_config

def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AWS Lambda处理函数
    也可以用于GitHub Actions或其他环境
    """
    try:
        # 解析请求体
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # 验证必需参数
        required_params = [
            'mysql_host', 'mysql_port', 'mysql_username', 
            'mysql_password', 'mysql_database',
            'app_token', 'personal_base_token'
        ]
        
        # region参数是可选的，默认为domestic
        region = body.get('region', 'domestic')
        
        missing_params = [param for param in required_params if not body.get(param)]
        if missing_params:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'缺少必需参数: {", ".join(missing_params)}'
                }, ensure_ascii=False)
            }
        
        # 执行同步
        results = sync_with_config(
            mysql_host=body['mysql_host'],
            mysql_port=int(body['mysql_port']),
            mysql_username=body['mysql_username'],
            mysql_password=body['mysql_password'],
            mysql_database=body['mysql_database'],
            app_token=body['app_token'],
            personal_base_token=body['personal_base_token'],
            region=region
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': '同步完成',
                'results': results
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
        }

def main():
    """
    命令行模式，用于GitHub Actions
    """
    try:
        # 从环境变量读取配置
        config = {
            'mysql_host': os.getenv('MYSQL_HOST'),
            'mysql_port': int(os.getenv('MYSQL_PORT', '3306')),
            'mysql_username': os.getenv('MYSQL_USERNAME'),
            'mysql_password': os.getenv('MYSQL_PASSWORD'),
            'mysql_database': os.getenv('MYSQL_DATABASE'),
            'app_token': os.getenv('APP_TOKEN'),
            'personal_base_token': os.getenv('PERSONAL_BASE_TOKEN'),
            'region': os.getenv('REGION', 'domestic')
        }
        
        # 验证配置
        missing_vars = [k for k, v in config.items() if not v]
        if missing_vars:
            print(f"错误: 缺少环境变量: {', '.join(missing_vars)}")
            sys.exit(1)
        
        print("开始同步...")
        results = sync_with_config(**config)
        
        print("同步完成!")
        print(f"同步结果: {results}")
        
        # 输出结果到GitHub Actions
        if os.getenv('GITHUB_ACTIONS'):
            with open(os.getenv('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
                f.write(f"sync_results={json.dumps(results)}\n")
        
    except Exception as e:
        print(f"同步失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()