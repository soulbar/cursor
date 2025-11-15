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
from urllib.parse import urlparse, parse_qsl, unquote
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

SUPPORTED_PROXY_PREFIXES = (
    'ss://', 'vmess://', 'trojan://', 'vless://',
    'hysteria2://', 'hysteria://', 'tuic://', 'wireguard://',
    'http://', 'https://', 'socks://', 'socks5://'
)


def is_supported_proxy_url(line):
    return any(line.startswith(prefix) for prefix in SUPPORTED_PROXY_PREFIXES)


def parse_proxy_url(proxy_url):
    """解析代理URL（ss://, vmess://, trojan://, vless://等）"""
    node = {}

    def str_to_bool(value):
        if value is None:
            return False
        return str(value).strip().lower() in ['1', 'true', 'yes', 'on']

    def to_int(value):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None

    if proxy_url.startswith('vless://'):
        # VLESS格式: vless://uuid@server:port?params#name
        try:
            parts = proxy_url[8:].split('#')
            name = parts[1] if len(parts) > 1 else ''
            
            main_part = parts[0].split('?')
            if len(main_part) >= 1:
                server_part = main_part[0].split('@')
                if len(server_part) == 2:
                    uuid = server_part[0]
                    server_port = server_part[1].split(':')
                    if len(server_port) == 2:
                        node = {
                            'name': name or f"VLESS-{server_port[0]}:{server_port[1]}",
                            'type': 'vless',
                            'server': server_port[0],
                            'port': int(server_port[1]),
                            'uuid': uuid,
                            'tls': False
                        }
                        # 解析参数
                        if len(main_part) > 1:
                            params = main_part[1].split('&')
                            for param in params:
                                if '=' in param:
                                    key, value = param.split('=', 1)
                                    value = unquote(value)
                                    
                                    if key == 'type':
                                        node['network'] = value
                                    elif key == 'security':
                                        if value == 'tls' or value == 'reality':
                                            node['tls'] = True
                                            if value == 'reality':
                                                node['type'] = 'vless'  # Reality是VLESS的变体
                                    elif key == 'sni':
                                        node['servername'] = value
                                    elif key == 'host':
                                        if 'ws-opts' not in node:
                                            node['ws-opts'] = {}
                                        if 'headers' not in node['ws-opts']:
                                            node['ws-opts']['headers'] = {}
                                        node['ws-opts']['headers']['Host'] = value
                                    elif key == 'path':
                                        if 'ws-opts' not in node:
                                            node['ws-opts'] = {}
                                        node['ws-opts']['path'] = value
                                    # Reality 参数
                                    elif key == 'pbk' or key == 'public-key':
                                        if 'reality-opts' not in node:
                                            node['reality-opts'] = {}
                                        node['reality-opts']['public-key'] = value
                                    elif key == 'sid' or key == 'short-id':
                                        if 'reality-opts' not in node:
                                            node['reality-opts'] = {}
                                        node['reality-opts']['short-id'] = value
                                    elif key == 'fp' or key == 'client-fingerprint':
                                        node['client-fingerprint'] = value
        except Exception as e:
            pass
    
    elif proxy_url.startswith('ss://'):
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
    
    elif proxy_url.startswith('hysteria2://') or proxy_url.startswith('hysteria://'):
        # Hysteria2格式: hysteria2://password@server:port?params#name
        # 也支持旧版hysteria://
        try:
            protocol_prefix = 'hysteria2://' if proxy_url.startswith('hysteria2://') else 'hysteria://'
            parts = proxy_url[len(protocol_prefix):].split('#')
            name = parts[1] if len(parts) > 1 else ''
            
            main_part = parts[0].split('?')
            if len(main_part) >= 1:
                server_part = main_part[0].split('@')
                if len(server_part) == 2:
                    password = server_part[0]
                    server_port = server_part[1].split(':')
                    if len(server_port) == 2:
                        node = {
                            'name': name or f"Hysteria2-{server_port[0]}:{server_port[1]}",
                            'type': 'hysteria2',
                            'server': server_port[0],
                            'port': int(server_port[1]),
                            'password': password
                        }
                        
                        # 解析参数
                        if len(main_part) > 1:
                            params = main_part[1].split('&')
                            for param in params:
                                if '=' in param:
                                    key, value = param.split('=', 1)
                                    value = unquote(value)
                                    
                                    if key == 'sni' or key == 'peer':
                                        node['sni'] = value
                                    elif key == 'insecure':
                                        if value.lower() in ['true', '1', 'yes']:
                                            node['skip-cert-verify'] = True
                                    elif key == 'obfs':
                                        if 'obfs' not in node:
                                            node['obfs'] = {}
                                        if value.startswith('salamander'):
                                            # salamander:password
                                            obfs_parts = value.split(':')
                                            if len(obfs_parts) == 2:
                                                node['obfs']['type'] = 'salamander'
                                                node['obfs']['password'] = obfs_parts[1]
                                    elif key == 'obfs-password':
                                        if 'obfs' not in node:
                                            node['obfs'] = {}
                                        if 'type' not in node['obfs']:
                                            node['obfs']['type'] = 'salamander'
                                        node['obfs']['password'] = value
                                    elif key == 'bandwidth' or key == 'up' or key == 'down':
                                        # Hysteria2 带宽设置
                                        if 'bandwidth' not in node:
                                            node['bandwidth'] = {}
                                        if key == 'up':
                                            node['bandwidth']['up'] = value
                                        elif key == 'down':
                                            node['bandwidth']['down'] = value
        except Exception as e:
            pass

    elif proxy_url.startswith('tuic://'):
        try:
            parsed = urlparse(proxy_url)
            params = {k.lower(): v for k, v in parse_qsl(parsed.query)}

            server = parsed.hostname or params.get('server') or params.get('host')
            if not server and params.get('endpoint'):
                endpoint = params['endpoint']
                if ':' in endpoint:
                    server = endpoint.rsplit(':', 1)[0]

            port = parsed.port
            if port is None:
                port_value = params.get('port')
                if not port_value and params.get('endpoint') and ':' in params['endpoint']:
                    port_value = params['endpoint'].rsplit(':', 1)[1]
                port = to_int(port_value)

            if server and port:
                name = parsed.fragment or params.get('name') or f"TUIC-{server}:{port}"
                node = {
                    'name': name,
                    'type': 'tuic',
                    'server': server,
                    'port': port
                }

                if parsed.username and parsed.password:
                    node['uuid'] = parsed.username
                    node['password'] = parsed.password
                elif parsed.username and not parsed.password:
                    node['password'] = parsed.username

                if 'uuid' in params:
                    node['uuid'] = params['uuid']
                if 'password' in params:
                    node['password'] = params['password']

                sni = params.get('sni') or params.get('peer') or params.get('servername')
                if sni:
                    node['sni'] = sni

                if 'alpn' in params:
                    alpn_values = [item.strip() for item in params['alpn'].split(',') if item.strip()]
                    if alpn_values:
                        node['alpn'] = alpn_values

                congestion = params.get('congestion-control') or params.get('congestion_control')
                if congestion:
                    node['congestion-control'] = congestion

                udp_mode = params.get('udp-relay-mode') or params.get('udp_relay_mode')
                if udp_mode:
                    node['udp-relay-mode'] = udp_mode

                heartbeat = params.get('heartbeat-interval') or params.get('heartbeat_interval')
                heartbeat_value = to_int(heartbeat)
                if heartbeat_value is not None:
                    node['heartbeat-interval'] = heartbeat_value

                if any(key in params for key in ['skip-cert-verify', 'allow-insecure', 'allow_insecure', 'insecure']):
                    key = next(k for k in ['skip-cert-verify', 'allow-insecure', 'allow_insecure', 'insecure'] if k in params)
                    if str_to_bool(params[key]):
                        node['skip-cert-verify'] = True

                if any(key in params for key in ['disable-sni', 'disable_sni']):
                    key = 'disable-sni' if 'disable-sni' in params else 'disable_sni'
                    if str_to_bool(params[key]):
                        node['disable-sni'] = True

                if any(key in params for key in ['zero-rtt-handshake', 'zero_rtt_handshake']):
                    key = 'zero-rtt-handshake' if 'zero-rtt-handshake' in params else 'zero_rtt_handshake'
                    if str_to_bool(params[key]):
                        node['zero-rtt-handshake'] = True

                if any(key in params for key in ['reduce-rtt', 'reduce_rtt']):
                    key = 'reduce-rtt' if 'reduce-rtt' in params else 'reduce_rtt'
                    if str_to_bool(params[key]):
                        node['reduce-rtt'] = True
        except Exception:
            pass

    elif proxy_url.startswith('wireguard://'):
        try:
            parsed = urlparse(proxy_url)
            params = {k.lower(): v for k, v in parse_qsl(parsed.query)}

            server = parsed.hostname or params.get('server') or params.get('host') or params.get('hostname')
            if not server and params.get('endpoint'):
                endpoint = params['endpoint']
                if ':' in endpoint:
                    server = endpoint.rsplit(':', 1)[0]

            port = parsed.port
            if port is None:
                port_value = params.get('port')
                if not port_value and params.get('endpoint') and ':' in params['endpoint']:
                    port_value = params['endpoint'].rsplit(':', 1)[1]
                port = to_int(port_value)

            if server and port:
                name = parsed.fragment or params.get('name') or f"WireGuard-{server}:{port}"
                node = {
                    'name': name,
                    'type': 'wireguard',
                    'server': server,
                    'port': port
                }

                private_key = params.get('private-key') or params.get('private_key') or params.get('privatekey')
                if private_key:
                    node['private-key'] = private_key
                elif parsed.username:
                    node['private-key'] = parsed.username

                pre_shared = params.get('pre-shared-key') or params.get('pre_shared_key') or params.get('presharedkey') or params.get('psk')
                if pre_shared:
                    node['pre-shared-key'] = pre_shared
                elif parsed.password:
                    node['pre-shared-key'] = parsed.password

                public_key = params.get('public-key') or params.get('public_key') or params.get('publickey')
                if public_key:
                    node['public-key'] = public_key

                ip = params.get('ip') or params.get('address') or params.get('local-address')
                if ip:
                    node['ip'] = ip

                dns = params.get('dns') or params.get('dns-server') or params.get('dns_servers')
                if dns:
                    dns_values = [item.strip() for item in re.split(r'[;,]', dns) if item.strip()]
                    if dns_values:
                        node['dns'] = dns_values

                mtu_value = to_int(params.get('mtu'))
                if mtu_value is not None:
                    node['mtu'] = mtu_value

                keepalive_value = to_int(params.get('keepalive') or params.get('persistent-keepalive'))
                if keepalive_value is not None:
                    node['keepalive'] = keepalive_value

                if 'reserved' in params:
                    raw_reserved = params['reserved']
                    reserved_values = []
                    for item in re.split(r'[;,]', raw_reserved):
                        item = item.strip()
                        if not item:
                            continue
                        try:
                            reserved_values.append(int(item, 0))
                        except ValueError:
                            try:
                                reserved_values.append(int(item))
                            except ValueError:
                                pass
                    if reserved_values:
                        node['reserved'] = reserved_values

                if any(key in params for key in ['udp', 'udp-relay', 'udp_relay']):
                    key = next(k for k in ['udp', 'udp-relay', 'udp_relay'] if k in params)
                    if str_to_bool(params[key]):
                        node['udp'] = True

                if params.get('sni') or params.get('servername'):
                    node['servername'] = params.get('sni') or params.get('servername')
        except Exception:
            pass

    elif proxy_url.startswith('http://') or proxy_url.startswith('https://'):
        try:
            parsed = urlparse(proxy_url)
            server = parsed.hostname
            port = parsed.port or (443 if proxy_url.startswith('https://') else 80)

            if server and port:
                scheme = 'HTTPS' if proxy_url.startswith('https://') else 'HTTP'
                name = parsed.fragment or f"{scheme}-{server}:{port}"
                node = {
                    'name': name,
                    'type': 'http',
                    'server': server,
                    'port': port
                }

                if parsed.username:
                    node['username'] = parsed.username
                if parsed.password:
                    node['password'] = parsed.password

                if proxy_url.startswith('https://'):
                    node['tls'] = True

                params = {k.lower(): v for k, v in parse_qsl(parsed.query)}

                if any(key in params for key in ['skip-cert-verify', 'allow-insecure', 'allow_insecure', 'insecure']):
                    key = next(k for k in ['skip-cert-verify', 'allow-insecure', 'allow_insecure', 'insecure'] if k in params)
                    if str_to_bool(params[key]):
                        node['skip-cert-verify'] = True

                if params.get('sni') or params.get('servername'):
                    node['servername'] = params.get('sni') or params.get('servername')
        except Exception:
            pass

    elif proxy_url.startswith('socks://') or proxy_url.startswith('socks5://'):
        try:
            parsed = urlparse(proxy_url)
            server = parsed.hostname
            port = parsed.port or 1080

            if server and port:
                name = parsed.fragment or f"SOCKS5-{server}:{port}"
                node = {
                    'name': name,
                    'type': 'socks5',
                    'server': server,
                    'port': port
                }

                if parsed.username:
                    node['username'] = parsed.username
                if parsed.password:
                    node['password'] = parsed.password

                params = {k.lower(): v for k, v in parse_qsl(parsed.query)}

                if any(key in params for key in ['udp', 'udp-relay', 'udp_relay']):
                    key = next(k for k in ['udp', 'udp-relay', 'udp_relay'] if k in params)
                    if str_to_bool(params[key]):
                        node['udp'] = True
        except Exception:
            pass

    return node if node.get('server') else None

def fetch_subscription(url, timeout=30):
    """获取订阅链接内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # 先尝试普通requests（禁用SSL验证）
        response = None
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
                print(f"  ⚠️  请求失败: {str(e2)[:100]}")
                return None
        
        if not response:
            return None
        
        content = response.text.strip()
        content_type = response.headers.get('Content-Type', '').lower()
        
        # 尝试解析为JSON格式（Clash配置）
        if 'json' in content_type or content.startswith('{'):
            try:
                config = json.loads(content)
                if isinstance(config, dict) and 'proxies' in config:
                    nodes = config['proxies']
                    print(f"  ✓ 解析为JSON格式，找到 {len(nodes)} 个节点")
                    return nodes
            except Exception as e:
                pass
        
        # 尝试解析为YAML格式（Clash配置）
        try:
            config = yaml.safe_load(content)
            if isinstance(config, dict) and 'proxies' in config:
                nodes = config['proxies']
                print(f"  ✓ 解析为YAML格式，找到 {len(nodes)} 个节点")
                return nodes
        except Exception as e:
            pass
        
        # 尝试解析为Base64编码的代理列表
        decoded = decode_base64(content)
        if decoded:
            lines = decoded.split('\n')
            nodes = []
            for line in lines:
                line = line.strip()
                if line and is_supported_proxy_url(line):
                    node = parse_proxy_url(line)
                    if node:
                        nodes.append(node)
            if nodes:
                print(f"  ✓ 解析为Base64编码格式，找到 {len(nodes)} 个节点")
                return nodes
        
        # 尝试直接解析为代理列表（每行一个）
        lines = content.split('\n')
        nodes = []
        for line in lines:
            line = line.strip()
            if line and is_supported_proxy_url(line):
                node = parse_proxy_url(line)
                if node:
                    nodes.append(node)
        
        if nodes:
            print(f"  ✓ 解析为纯文本格式，找到 {len(nodes)} 个节点")
            return nodes
        
        # 如果都没有解析成功，打印内容预览以便调试
        content_preview = content[:200] if len(content) > 200 else content
        print(f"  ⚠️  无法解析内容格式，内容预览: {content_preview}...")
        return None
        
    except Exception as e:
        print(f"  ❌ 获取订阅链接失败: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return None

def sanitize_node_name(name):
    """清理节点名称，移除可能导致问题的特殊字符"""
    if not name:
        return name
    
    import re
    name = name.strip()
    
    # 移除控制字符
    name = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', name)
    
    # 移除末尾已有的 "(数字)" 以免重复
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    
    # 仅保留常见字符：中英文字母、数字、常用符号，其他替换为空
    allowed_pattern = r'[^0-9A-Za-z\u4e00-\u9fff\-\_\.\s\[\]\(\):/|]'
    name = re.sub(allowed_pattern, '', name)
    
    # 合并连续空格
    name = re.sub(r'\s+', ' ', name)
    
    # 限制长度
    if len(name) > 80:
        name = name[:80]
    
    return name or None

def ensure_unique_name(name, seen_names, name_counters):
    """确保节点名称唯一"""
    if not name:
        return None
    
    base_name = name
    counter = name_counters.get(base_name, 0)
    
    unique_name = base_name if counter == 0 else f"{base_name}-{counter}"
    counter += 1
    
    while unique_name in seen_names:
        unique_name = f"{base_name}-{counter}"
        counter += 1
    
    seen_names.add(unique_name)
    name_counters[base_name] = counter
    return unique_name

def fetch_all_subscriptions(urls):
    """获取所有订阅链接的节点"""
    all_nodes = []
    seen_names = set()
    seen_identifiers = set()  # 用于去重：server:port:type:uuid的组合
    name_counters = {}  # 用于记录每个基础名称的计数
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 正在获取订阅: {url}")
        nodes = fetch_subscription(url)
        if nodes and len(nodes) > 0:
            added_count = 0
            for node in nodes:
                # 生成唯一标识符用于去重（基于server、port、type、uuid等）
                server = node.get('server', '')
                port = node.get('port', 0)
                node_type = node.get('type', '')
                uuid = node.get('uuid', '') or node.get('password', '') or ''  # UUID或密码作为标识
                identifier = f"{node_type}:{server}:{port}:{uuid}"
                
                # 如果标识符已存在，跳过（真正的重复节点）
                if identifier in seen_identifiers:
                    continue
                
                seen_identifiers.add(identifier)
                
                # 获取并清理节点名称
                node_name = node.get('name', '')
                node_name = sanitize_node_name(node_name)
                
                # 如果名称为空，生成一个
                if not node_name:
                    node_name = f"{node_type}-{server}-{port}"
                
                # 确保名称唯一
                unique_name = ensure_unique_name(node_name, seen_names, name_counters)
                if not unique_name:
                    fallback_name = f"{node_type}-{server}-{port}-{uuid[:8] if uuid else i}"
                    unique_name = ensure_unique_name(fallback_name, seen_names, name_counters)
                
                node['name'] = unique_name
                all_nodes.append(node)
                added_count += 1
            
            print(f"  ✓ 从该订阅添加了 {added_count} 个节点（去重后）")
        else:
            print(f"  ✗ 未获取到节点")
    
    # 最终检查：确保所有节点名称唯一
    final_names = {}
    duplicate_count = 0
    for node in all_nodes:
        node_name = node.get('name', '')
        if node_name in final_names:
            duplicate_count += 1
            # 为重复的名称添加后缀
            counter = final_names[node_name] + 1
            new_name = f"{node_name}-{counter}"
            while new_name in final_names:
                counter += 1
                new_name = f"{node_name}-{counter}"
            node['name'] = new_name
            final_names[new_name] = 1
        else:
            final_names[node_name] = 1
    
    if duplicate_count > 0:
        print(f"  ⚠️  检测到 {duplicate_count} 个重复名称，已自动修复")
    
    print(f"\n{'='*60}")
    print(f"总共获取到 {len(all_nodes)} 个唯一节点")
    print(f"{'='*60}")
    return all_nodes

if __name__ == "__main__":
    from config import SUBSCRIPTION_URLS
    nodes = fetch_all_subscriptions(SUBSCRIPTION_URLS)
    print(f"\n节点列表:")
    for node in nodes[:5]:  # 只显示前5个
        print(f"  - {node.get('name')} ({node.get('type')})")

