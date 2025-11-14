#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clash配置生成模块
"""
import yaml
from config import CLASH_CONFIG_TEMPLATE, RULES

def generate_clash_config(nodes):
    """生成Clash配置文件"""
    
    # 复制模板配置
    config = CLASH_CONFIG_TEMPLATE.copy()
    
    # 按延迟排序节点
    sorted_nodes = sorted(nodes, key=lambda x: x.get('latency', 9999))
    
    # 添加节点列表
    config['proxies'] = sorted_nodes
    
    # 创建代理组
    proxy_groups = [
        {
            "name": "🚀 自动选择",
            "type": "url-test",
            "proxies": [node['name'] for node in sorted_nodes],
            "url": "http://www.gstatic.com/generate_204",
            "interval": 300,
            "tolerance": 50
        },
        {
            "name": "🔯 手动选择",
            "type": "select",
            "proxies": ["🚀 自动选择"] + [node['name'] for node in sorted_nodes]
        },
        {
            "name": "⚡ 最快节点",
            "type": "url-test",
            "proxies": [node['name'] for node in sorted_nodes[:20]],  # 只测试前20个
            "url": "http://www.gstatic.com/generate_204",
            "interval": 300,
            "tolerance": 50
        }
    ]
    
    # 为每个分流规则创建代理组
    for rule_name in RULES.keys():
        proxy_groups.append({
            "name": rule_name,
            "type": "select",
            "proxies": ["🚀 自动选择", "⚡ 最快节点", "🔯 手动选择"] + [node['name'] for node in sorted_nodes[:5]]
        })
    
    # 添加必要的代理组
    proxy_groups.extend([
        {
            "name": "🎯 全球直连",
            "type": "select",
            "proxies": ["DIRECT"]
        },
        {
            "name": "🛑 全球拦截",
            "type": "select",
            "proxies": ["REJECT", "DIRECT"]
        },
        {
            "name": "🐟 漏网之鱼",
            "type": "select",
            "proxies": ["🚀 自动选择", "🎯 全球直连"]
        }
    ])
    
    config['proxy-groups'] = proxy_groups
    
    # 生成分流规则
    rules = []
    
    # 本地地址直连
    rules.extend([
        "DOMAIN-SUFFIX,local,DIRECT",
        "IP-CIDR,127.0.0.0/8,DIRECT",
        "IP-CIDR,172.16.0.0/12,DIRECT",
        "IP-CIDR,192.168.0.0/16,DIRECT",
        "IP-CIDR,10.0.0.0/8,DIRECT",
        "IP-CIDR,17.0.0.0/8,DIRECT",
        "IP-CIDR,100.64.0.0/10,DIRECT",
        "GEOIP,CN,🎯 全球直连"
    ])
    
    # 添加自定义分流规则
    for rule_name, rule_list in RULES.items():
        for rule in rule_list:
            rules.append(f"{rule},{rule_name}")
    
    # 广告拦截
    rules.extend([
        "DOMAIN-SUFFIX,ad.com,🛑 全球拦截",
        "DOMAIN-SUFFIX,ads.com,🛑 全球拦截",
        "DOMAIN-SUFFIX,doubleclick.net,🛑 全球拦截"
    ])
    
    # 默认规则
    rules.append("MATCH,🐟 漏网之鱼")
    
    config['rules'] = rules
    
    return config

def save_clash_config(config, filename='clash-config.yaml'):
    """保存Clash配置到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"配置文件已保存: {filename}")
        return True
    except Exception as e:
        print(f"保存配置文件失败: {str(e)}")
        return False

if __name__ == "__main__":
    from fetch_subscriptions import fetch_all_subscriptions
    from test_nodes import test_nodes
    from config import SUBSCRIPTION_URLS, MAX_LATENCY
    
    print("获取节点...")
    nodes = fetch_all_subscriptions(SUBSCRIPTION_URLS)
    
    print("\n开始测速...")
    available_nodes = test_nodes(nodes, MAX_LATENCY)
    
    print("\n生成Clash配置...")
    config = generate_clash_config(available_nodes)
    
    save_clash_config(config)
    print(f"\n配置完成！包含 {len(available_nodes)} 个可用节点")

