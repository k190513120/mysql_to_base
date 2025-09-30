#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试api.py的环境变量处理修复
"""

import os
import sys
import subprocess

def test_empty_env_vars():
    """
    测试空环境变量的处理
    """
    print("测试空环境变量处理...")
    
    # 设置测试环境变量（模拟GitHub Action中的空值情况）
    test_env = os.environ.copy()
    test_env.update({
        'MYSQL_HOST': 'test-host',
        'MYSQL_PORT': '',  # 空字符串
        'MYSQL_USERNAME': '',  # 空字符串
        'MYSQL_PASSWORD': 'test-password',
        'MYSQL_DATABASE': 'test-db',
        'APP_TOKEN': 'test-token',
        'PERSONAL_BASE_TOKEN': 'test-base-token',
        'REGION': 'domestic',
        'GITHUB_ACTIONS': 'true'
    })
    
    # 运行api.py并捕获输出
    try:
        result = subprocess.run(
            [sys.executable, 'api.py'],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"返回码: {result.returncode}")
        print(f"标准输出: {result.stdout}")
        print(f"标准错误: {result.stderr}")
        
        # 检查是否正确识别了缺失的环境变量
        if result.returncode == 1 and 'MYSQL_USERNAME' in result.stdout:
            print("✅ 测试通过：正确识别了缺失的环境变量")
            return True
        else:
            print("❌ 测试失败：未正确处理空环境变量")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_valid_env_vars():
    """
    测试有效环境变量的处理
    """
    print("\n测试有效环境变量处理...")
    
    # 设置有效的测试环境变量
    test_env = os.environ.copy()
    test_env.update({
        'MYSQL_HOST': 'localhost',
        'MYSQL_PORT': '3306',
        'MYSQL_USERNAME': 'test_user',
        'MYSQL_PASSWORD': 'test_pass',
        'MYSQL_DATABASE': 'test_db',
        'APP_TOKEN': 'test_app_token',
        'PERSONAL_BASE_TOKEN': 'test_personal_token',
        'REGION': 'domestic',
        'GITHUB_ACTIONS': 'true'
    })
    
    try:
        result = subprocess.run(
            [sys.executable, 'api.py'],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"返回码: {result.returncode}")
        print(f"标准输出: {result.stdout}")
        print(f"标准错误: {result.stderr}")
        
        # 这个测试预期会因为无法连接到MySQL而失败，但不应该是环境变量问题
        if '缺失或为空' not in result.stdout:
            print("✅ 测试通过：环境变量解析正常")
            return True
        else:
            print("❌ 测试失败：仍然报告环境变量缺失")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == '__main__':
    print("开始测试api.py的环境变量处理修复...")
    
    test1_passed = test_empty_env_vars()
    test2_passed = test_valid_env_vars()
    
    print("\n=== 测试结果 ===")
    print(f"空环境变量测试: {'通过' if test1_passed else '失败'}")
    print(f"有效环境变量测试: {'通过' if test2_passed else '失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！环境变量处理修复成功。")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，需要进一步修复。")
        sys.exit(1)