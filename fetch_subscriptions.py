#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订阅链接获取和解析模块
"""
import base64
import re
import requests
import yaml
import json
from urllib.parse import urlparse
import cloudscraper
import urllib3
import ssl

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建不验证证书的SSL上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def decode_base64(content):
    """解码Base64内容"""
    try:
        decoded = base64.b64decode(content)
        return decoded.decode('utf-8')
    except:
        return None

def parse_proxy_url(proxy_url):
    """解析代理URL（ss://, vmess://, trojan://等）"""
    node = {}
    
    if proxy_url.startswith('ss://'):
        # SS格式: ss://base64(method:password)@server:port#name
        try:
            parts = proxy_url[5:].split('#')
            name = parts[1] if len(parts) > 1 else ''
            
            main_part = parts[0].split('@')
            if len(main_part) == 2:
                server_port = main_part[1].split(':')
                if len(server_port) == 2:
                    decoded = decode_base64(main_part[0] + '==')
                    if decoded:
                        method_password = decoded.split(':')
                        if len(method_password) == 2:
                            node = {
                                'name': name or f"SS-{server_port[0]}:{server_port[1]}",
                                'type': 'ss',
                                'server': server_port[0],
                                'port': int(server_port[1]),
                                'cipher': method_password[0],
                                'password': method_password[1]
                            }
        except:
            pass
    
    elif proxy_url.startswith('vmess://'):
        # VMess格式: vmess://base64(json)
        try:
            decoded = decode_base64(proxy_url[8:])
            if decoded:
                vmess_config = json.loads(decoded)
                node = {
                    'name': vmess_config.get('ps', vmess_config.get('add', 'VMess')),
                    'type': 'vmess',
                    'server': vmess_config.get('add', ''),
                    'port': int(vmess_config.get('port', 0)),
                    'uuid': vmess_config.get('id', ''),
                    'cipher': vmess_config.get('scy', 'auto'),
                    'network': vmess_config.get('net', 'tcp')
                }
                
                # alterId字段（旧版VMess需要）
                aid = vmess_config.get('aid', 0)
                if aid:
                    node['alterId'] = int(aid)
                
                # WebSocket配置
                if vmess_config.get('net') == 'ws':
                    ws_opts = {
                        'path': vmess_config.get('path', '/')
                    }
                    host = vmess_config.get('host', '')
                    if host:
                        ws_opts['headers'] = {'Host': host}
                    node['ws-opts'] = ws_opts
                
                # TLS配置
                if vmess_config.get('tls') in ['tls', '1']:
                    node['tls'] = True
                    sni = vmess_config.get('sni') or vmess_config.get('host', '')
                    if sni:
                        node['servername'] = sni
                
                # skip-cert-verify (如果需要)
                if vmess_config.get('skip-cert-verify'):
                    node['skip-cert-verify'] = True
        except Exception as e:
            pass
    
    elif proxy_url.startswith('trojan://'):
        # Trojan格式: trojan://password@server:port#name
        try:
            parts = proxy_url[9:].split('#')
            name = parts[1] if len(parts) > 1 else ''
            
            main_part = parts[0].split('@')
            if len(main_part) == 2:
                server_port = main_part[1].split(':')
                if len(server_port) == 2:
                    password = main_part[0]
                    node = {
                        'name': name or f"Trojan-{server_port[0]}:{server_port[1]}",
                        'type': 'trojan',
                        'server': server_port[0],
                        'port': int(server_port[1]),
                        'password': password
                    }
        except:
            pass
    
    return node if node.get('server') else None

def fetch_subscription(url, timeout=30):
    """获取订阅链接内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # 先尝试普通requests（禁用SSL验证）
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=timeout, 
                allow_redirects=True,
                verify=False
            )
            response.raise_for_status()
        except Exception as e:
            # 如果失败，尝试使用cloudscraper
            try:
                scraper = cloudscraper.create_scraper(
                    browser={
                        'browser': 'chrome',
                        'platform': 'windows',
                        'desktop': True
                    },
                    verify=False
                )
                response = scraper.get(
                    url, 
                    headers=headers, 
                    timeout=timeout, 
                    allow_redirects=True
                )
                response.raise_for_status()
            except Exception as e2:
                raise e2
        
        content = response.text.strip()
        
        # 尝试解析为YAML格式（Clash配置）
        try:
            config = yaml.safe_load(content)
            if isinstance(config, dict) and 'proxies' in config:
                return config['proxies']
        except:
            pass
        
        # 尝试解析为Base64编码的代理列表
        decoded = decode_base64(content)
        if decoded:
            lines = decoded.split('\n')
            nodes = []
            for line in lines:
                line = line.strip()
                if line and (line.startswith('ss://') or line.startswith('vmess://') or 
                           line.startswith('trojan://') or line.startswith('vless://')):
                    node = parse_proxy_url(line)
                    if node:
                        nodes.append(node)
            if nodes:
                return nodes
        
        # 尝试直接解析为代理列表（每行一个）
        lines = content.split('\n')
        nodes = []
        for line in lines:
            line = line.strip()
            if line and (line.startswith('ss://') or line.startswith('vmess://') or 
                       line.startswith('trojan://') or line.startswith('vless://')):
                node = parse_proxy_url(line)
                if node:
                    nodes.append(node)
        
        return nodes if nodes else None
        
    except Exception as e:
        print(f"获取订阅链接失败 {url}: {str(e)}")
        return None

def fetch_all_subscriptions(urls):
    """获取所有订阅链接的节点"""
    all_nodes = []
    seen_names = set()
    
    for url in urls:
        print(f"正在获取订阅: {url}")
        nodes = fetch_subscription(url)
        if nodes:
            for node in nodes:
                # 去重（基于节点名称）
                node_name = node.get('name', '')
                if node_name and node_name not in seen_names:
                    seen_names.add(node_name)
                    all_nodes.append(node)
                elif not node_name:
                    # 如果没有名称，尝试生成唯一名称
                    server = node.get('server', 'unknown')
                    port = node.get('port', 0)
                    unique_name = f"{node.get('type', 'proxy')}-{server}-{port}"
                    if unique_name not in seen_names:
                        seen_names.add(unique_name)
                        node['name'] = unique_name
                        all_nodes.append(node)
            print(f"  获取到 {len(nodes)} 个节点")
        else:
            print(f"  未获取到节点")
    
    print(f"\n总共获取到 {len(all_nodes)} 个唯一节点")
    return all_nodes

if __name__ == "__main__":
    from config import SUBSCRIPTION_URLS
    nodes = fetch_all_subscriptions(SUBSCRIPTION_URLS)
    print(f"\n节点列表:")
    for node in nodes[:5]:  # 只显示前5个
        print(f"  - {node.get('name')} ({node.get('type')})")

