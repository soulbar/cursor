#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主执行脚本
"""
import argparse
import sys
import os
from datetime import datetime
from fetch_subscriptions import (
    fetch_all_subscriptions,
    fetch_subscription,
    sanitize_node_name,
    ensure_unique_name,
)
from test_nodes import test_nodes
from generate_clash import generate_clash_config, save_clash_config
from config import SUBSCRIPTION_URLS, MAX_LATENCY, TEST_TIMEOUT


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="订阅节点汇聚工具")
    parser.add_argument(
        "--list",
        action="store_true",
        help="仅列出节点信息，不执行测速和配置生成",
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        help="指定订阅链接，多个链接使用空格分隔（默认使用 config.py 中的配置）",
    )
    parser.add_argument(
        "--max-latency",
        type=int,
        help="覆盖默认的最大延迟阈值（毫秒）",
    )
    return parser.parse_args()


def format_node_line(index, node):
    """格式化节点信息便于展示"""
    node_type = node.get("type", "unknown").upper()
    server = node.get("server", "?")
    port = node.get("port", "?")
    extras = []

    network = node.get("network")
    if network:
        extras.append(network.upper())

    if node.get("tls"):
        extras.append("TLS")

    if node_type == "SS":
        cipher = node.get("cipher")
        if cipher:
            extras.append(cipher)

    if node_type in {"VMESS", "VLESS"}:
        fingerprint = node.get("client-fingerprint")
        if fingerprint:
            extras.append(f"FP={fingerprint}")

    detail = f"{node_type} | {server}:{port}"
    if extras:
        detail += " | " + ", ".join(extras)

    return f"{index:>3}. {node.get('name', '未命名节点')} -> {detail}"


def list_subscription_nodes(urls):
    """列出指定订阅链接中的节点信息"""
    print("=" * 60)
    print("订阅节点列表模式")
    print("=" * 60)
    print(f"共 {len(urls)} 个订阅链接\n")

    aggregated_nodes = []
    aggregated_identifiers = set()

    for url in urls:
        print(f"正在获取订阅: {url}")
        nodes = fetch_subscription(url)
        if not nodes:
            print("  ✗ 未获取到节点\n")
            continue

        seen_names = set()
        name_counters = {}
        seen_identifiers = set()
        processed_nodes = []

        for node in nodes:
            server = node.get("server", "")
            port = node.get("port", 0)
            node_type = node.get("type", "")
            uuid = node.get("uuid", "") or node.get("password", "") or ""
            identifier = f"{node_type}:{server}:{port}:{uuid}"

            if identifier in seen_identifiers:
                continue
            seen_identifiers.add(identifier)

            node_name = sanitize_node_name(node.get("name", ""))
            if not node_name:
                node_name = f"{node_type or 'node'}-{server}-{port}"

            unique_name = ensure_unique_name(node_name, seen_names, name_counters)
            if not unique_name:
                fallback = f"{node_type or 'node'}-{server}-{port}-{uuid[:8]}"
                unique_name = ensure_unique_name(fallback, seen_names, name_counters)
            node["name"] = unique_name or node_name
            processed_nodes.append(node)

            if identifier not in aggregated_identifiers:
                aggregated_identifiers.add(identifier)
                aggregated_nodes.append(node)

        if not processed_nodes:
            print("  ✗ 订阅中没有可展示的节点\n")
            continue

        print(f"  ✓ 找到 {len(processed_nodes)} 个节点:\n")
        for index, node in enumerate(processed_nodes, 1):
            print("   " + format_node_line(index, node))
        print("")

    print("=" * 60)
    print(f"汇总唯一节点: {len(aggregated_nodes)}")
    print("=" * 60)
    return aggregated_nodes

def main():
    args = parse_args()
    target_urls = args.urls if args.urls else SUBSCRIPTION_URLS
    latency_threshold = args.max_latency if args.max_latency else MAX_LATENCY

    if args.list:
        list_subscription_nodes(target_urls)
        return

    print("=" * 60)
    print("订阅节点汇聚工具")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 获取订阅节点
    print("[1/3] 正在获取订阅节点...")
    try:
        nodes = fetch_all_subscriptions(target_urls)
        if not nodes:
            print("错误: 未获取到任何节点")
            sys.exit(1)
        print(f"✓ 成功获取 {len(nodes)} 个节点\n")
    except Exception as e:
        print(f"错误: 获取节点失败 - {str(e)}")
        sys.exit(1)

    # 2. 测速并过滤
    print(
        f"[2/3] 正在测试节点延迟（过滤延迟>{latency_threshold}ms的节点）..."
    )
    try:
        available_nodes = test_nodes(nodes, latency_threshold, TEST_TIMEOUT)
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

