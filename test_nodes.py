#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点测速模块
"""
import asyncio
import socket
import time
from concurrent.futures import ThreadPoolExecutor
import sys

# Windows下设置事件循环策略
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_node_latency(node, timeout=5):
    """测试节点延迟（TCP连接时间）"""
    server = node.get('server', '')
    port = node.get('port', 0)
    
    if not server or not port:
        return None
    
    try:
        start_time = time.time()
        
        # 使用asyncio创建TCP连接测试延迟
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(server, port),
                timeout=timeout
            )
            latency = (time.time() - start_time) * 1000  # 转换为毫秒
            writer.close()
            await writer.wait_closed()
            return round(latency, 2)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            return None
            
    except Exception as e:
        return None

def test_node_latency_sync(node, timeout=5):
    """同步版本的延迟测试（用于线程池）"""
    server = node.get('server', '')
    port = node.get('port', 0)
    
    if not server or not port:
        return None, None
    
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((server, port))
        latency = (time.time() - start_time) * 1000  # 转换为毫秒
        
        sock.close()
        
        if result == 0:  # 连接成功
            return node, round(latency, 2)
        else:
            return node, None
            
    except socket.timeout:
        return node, None
    except Exception as e:
        return node, None

async def test_nodes_async(nodes, max_latency=500, timeout=5, max_workers=50):
    """异步测试所有节点"""
    print(f"开始测试 {len(nodes)} 个节点...")
    
    # 使用线程池执行同步测速（避免某些网络库的异步问题）
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(executor, test_node_latency_sync, node, timeout)
            for node in nodes
        ]
        
        results = []
        completed = 0
        
        for coro in asyncio.as_completed(tasks):
            node, latency = await coro
            completed += 1
            
            if latency is not None:
                if latency <= max_latency:
                    node['latency'] = latency
                    results.append(node)
                    status = "✓ 通过"
                else:
                    status = f"✗ 延迟过高 ({latency}ms)"
            else:
                status = "✗ 连接失败"
            
            node_name = node.get('name', 'Unknown')
            print(f"  [{completed}/{len(nodes)}] {node_name[:40]:<40} {status}")
    
    print(f"\n测试完成！可用节点: {len(results)}/{len(nodes)}")
    return results

def test_nodes(nodes, max_latency=500, timeout=5):
    """测试节点延迟并过滤"""
    # 运行异步测试
    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(
            test_nodes_async(nodes, max_latency, timeout)
        )
        return results
    except Exception as e:
        print(f"异步测试失败，尝试同步测试: {str(e)}")
        # 如果异步失败，使用同步方式
        return test_nodes_sync(nodes, max_latency, timeout)

def test_nodes_sync(nodes, max_latency=500, timeout=5):
    """同步测试节点（备用方案）"""
    print(f"开始测试 {len(nodes)} 个节点（同步模式）...")
    results = []
    
    for i, node in enumerate(nodes, 1):
        server = node.get('server', '')
        port = node.get('port', 0)
        node_name = node.get('name', 'Unknown')
        
        if not server or not port:
            print(f"  [{i}/{len(nodes)}] {node_name[:40]:<40} ✗ 配置无效")
            continue
        
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            result = sock.connect_ex((server, port))
            latency = (time.time() - start_time) * 1000
            
            sock.close()
            
            if result == 0 and latency <= max_latency:
                node['latency'] = round(latency, 2)
                results.append(node)
                print(f"  [{i}/{len(nodes)}] {node_name[:40]:<40} ✓ 通过 ({node['latency']}ms)")
            elif result == 0:
                print(f"  [{i}/{len(nodes)}] {node_name[:40]:<40} ✗ 延迟过高 ({latency:.0f}ms)")
            else:
                print(f"  [{i}/{len(nodes)}] {node_name[:40]:<40} ✗ 连接失败")
                
        except socket.timeout:
            print(f"  [{i}/{len(nodes)}] {node_name[:40]:<40} ✗ 超时")
        except Exception as e:
            print(f"  [{i}/{len(nodes)}] {node_name[:40]:<40} ✗ 错误: {str(e)[:20]}")
    
    print(f"\n测试完成！可用节点: {len(results)}/{len(nodes)}")
    return results

if __name__ == "__main__":
    from fetch_subscriptions import fetch_all_subscriptions
    from config import SUBSCRIPTION_URLS, MAX_LATENCY
    
    print("获取节点...")
    nodes = fetch_all_subscriptions(SUBSCRIPTION_URLS)
    
    print("\n开始测速...")
    available_nodes = test_nodes(nodes, MAX_LATENCY)
    
    print(f"\n可用节点列表（延迟<{MAX_LATENCY}ms）:")
    for node in available_nodes[:10]:  # 显示前10个
        print(f"  - {node.get('name')} ({node.get('type')}) - {node.get('latency')}ms")

