#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主执行脚本
"""
import sys
import os
from datetime import datetime
from fetch_subscriptions import fetch_all_subscriptions
from test_nodes import test_nodes
from generate_clash import generate_clash_config, save_clash_config
from config import SUBSCRIPTION_URLS, MAX_LATENCY

def main():
    print("=" * 60)
    print("订阅节点汇聚工具")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 获取订阅节点
    print("[1/3] 正在获取订阅节点...")
    try:
        nodes = fetch_all_subscriptions(SUBSCRIPTION_URLS)
        if not nodes:
            print("错误: 未获取到任何节点")
            sys.exit(1)
        print(f"✓ 成功获取 {len(nodes)} 个节点\n")
    except Exception as e:
        print(f"错误: 获取节点失败 - {str(e)}")
        sys.exit(1)
    
    # 2. 测速并过滤
    print(f"[2/3] 正在测试节点延迟（过滤延迟>{MAX_LATENCY}ms的节点）...")
    try:
        available_nodes = test_nodes(nodes, MAX_LATENCY)
        if not available_nodes:
            print("错误: 没有可用的节点（所有节点延迟都超过阈值）")
            sys.exit(1)
        print(f"✓ 测试完成，可用节点: {len(available_nodes)}/{len(nodes)}\n")
    except Exception as e:
        print(f"错误: 测速失败 - {str(e)}")
        sys.exit(1)
    
    # 3. 生成Clash配置
    print("[3/3] 正在生成Clash配置文件...")
    try:
        config = generate_clash_config(available_nodes)
        
        # 保存到本地文件
        output_file = 'clash-config.yaml'
        if save_clash_config(config, output_file):
            print(f"✓ 配置文件已生成: {output_file}")
            print(f"  - 包含 {len(available_nodes)} 个可用节点")
            print(f"  - 包含 {len(config.get('rules', []))} 条分流规则")
            print(f"  - 包含 {len(config.get('proxy-groups', []))} 个代理组")
        else:
            print("错误: 保存配置文件失败")
            sys.exit(1)
    except Exception as e:
        print(f"错误: 生成配置失败 - {str(e)}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 如果是在GitHub Actions中运行，也保存到GITHUB_OUTPUT
    if os.environ.get('GITHUB_ACTIONS'):
        output_file_path = os.path.abspath(output_file)
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"config_file={output_file_path}\n")
            f.write(f"node_count={len(available_nodes)}\n")

if __name__ == "__main__":
    main()

