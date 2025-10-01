#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试国内飞书多维表格同步功能
验证修复后的主键去重逻辑
"""

import os
import sys
from mysql_to_base_sync import sync_with_config

def test_domestic_sync():
    """测试国内飞书多维表格同步"""
    print("开始测试国内飞书多维表格同步...")
    print("=" * 50)
    
    # 配置信息
    config = {
        'mysql_host': 'rm-zf81e68a31gsqv1c7zo.mysql.kualalumpur.rds.aliyuncs.com',
        'mysql_port': 3306,
        'mysql_username': 'writer_readonly',
        'mysql_password': 'c*xZ%BEu2VikL%G',
        'mysql_database': 'written',
        'app_token': 'EzA6b2iP0arQI7stUercb6iynnf',
        'personal_base_token': 'pt-D9cESyoW1NYgWf3pMA-D8LC-I2Ffu8K9X8rM3GiZAQAAAkCBYByAEF1qgICe',
        'region': 'domestic'
    }
    
    print("配置信息:")
    print(f"MySQL主机: {config['mysql_host']}")
    print(f"MySQL数据库: {config['mysql_database']}")
    print(f"飞书APP_TOKEN: {config['app_token']}")
    print(f"区域: {config['region']} (国内飞书)")
    print("=" * 50)
    
    try:
        # 执行同步
        results = sync_with_config(**config)
        
        print("\n同步完成!")
        print("=" * 50)
        print("同步结果:")
        
        if isinstance(results, dict):
            for table_name, result in results.items():
                print(f"表 {table_name}: {result}")
        else:
            print(f"结果: {results}")
            
        print("=" * 50)
        print("测试完成! 请检查:")
        print("1. 是否成功连接到MySQL数据库")
        print("2. 是否成功连接到国内飞书多维表格")
        print("3. 是否正确处理了主键去重逻辑")
        print("4. 日志中是否显示了更新vs新增的记录统计")
        print("5. 是否避免了重复数据问题")
        
        return True
        
    except Exception as e:
        print(f"\n同步失败: {e}")
        print("=" * 50)
        print("请检查:")
        print("1. MySQL数据库连接信息是否正确")
        print("2. 飞书多维表格配置是否有效")
        print("3. 网络连接是否正常")
        return False

if __name__ == '__main__':
    success = test_domestic_sync()
    sys.exit(0 if success else 1)