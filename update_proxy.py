import requests
import base64
import json
import argparse

def fetch_and_decode(url, ps_list=None, print_name=False, config_name=None):
    # 获取URL内容
    response = requests.get(url)
    if response.status_code == 200:
        # 获取响应内容
        encoded_content = response.text.strip()
        
        # Base64解码
        decoded_bytes = base64.b64decode(encoded_content)
        decoded_content = decoded_bytes.decode('utf-8')

        # 尝试将解码后的内容解析为JSON（如果是JSON格式）
        try:
            parsed_json = json.loads(decoded_content)
            print(json.dumps(parsed_json, indent=4, ensure_ascii=False))
        except json.JSONDecodeError:
            # 如果不是JSON格式，直接输出解码后的内容
            print(decoded_content)
        
        # 解析vmess行
        vmess_list = parse_vmess_lines(decoded_content)
        
        if print_name:
            print_all_ps(vmess_list)
        
        if ps_list:
            generate_config(vmess_list, ps_list, config_name)
    else:
        print(f"Failed to retrieve content. Status code: {response.status_code}")

def parse_vmess_lines(content):
    vmess_list = []
    lines = content.split('\n')
    for line in lines:
        if line.startswith('vmess://'):
            encoded_vmess = line[8:]  # 去掉 'vmess://' 前缀
            try:
                decoded_vmess = base64.b64decode(encoded_vmess).decode('utf-8')
                vmess_json = json.loads(decoded_vmess)
                print(json.dumps(vmess_json, indent=4, ensure_ascii=False))
                
                # 转换并打印特定JSON格式
                converted_json = convert_vmess_to_json(vmess_json)
                print(json.dumps(converted_json, indent=4, ensure_ascii=False))
                
                vmess_list.append(vmess_json)
            except (base64.binascii.Error, json.JSONDecodeError):
                print(f"Failed to decode vmess line: {line}")
    return vmess_list

def convert_vmess_to_json(vmess_json):
    try:
        address = vmess_json.get('add', '')
        port = int(vmess_json.get('port', 0))
        id = vmess_json.get('id', '')

        converted = {
            "settings": {
                "vnext": [
                    {
                        "address": address,
                        "port": port,
                        "users": [
                            {
                                "id": id,
                                "alterId": int(vmess_json.get('aid', 0)),  # 确保 alterId 是整数
                                "email": vmess_json.get('email', 't@t.tt'),
                                "security": vmess_json.get('scy', 'auto')
                            }
                        ]
                    }
                ]
            }
        }
        return converted
    except KeyError as e:
        print(f"Key error: {e}")
        return {}

def print_all_ps(vmess_list):
    print("ps values, ip, port, and id:")
    for vmess in vmess_list:
        ps = vmess.get('ps', 'N/A')
        ip = vmess.get('add', 'N/A')
        port = vmess.get('port', 'N/A')
        id = vmess.get('id', 'N/A')
        print(f"{ps} {ip} {port} {id}")

def generate_config(vmess_list, ps_list, config_name=None):
    outbounds = []
    for i, ps in enumerate(ps_list):
        # 查找与当前 ps 匹配的 vmess 条目
        matching_vmess = next((vmess for vmess in vmess_list if vmess.get('ps') == ps), None)
        
        if matching_vmess:
            address = matching_vmess.get('add', '')
            port = int(matching_vmess.get('port', 0))  # 从 vmess 数据中读取端口
            id = matching_vmess.get('id', '')
            tag = f"proxy{i+1}"

            # 打印匹配到的 vmess 信息
            print(f"Matching vmess for ps {ps}: {json.dumps(matching_vmess, indent=4, ensure_ascii=False)}")

            outbound = {
                "tag": tag,
                "protocol": "vmess",
                "settings": {
                    "vnext": [
                        {
                            "address": address,  # 使用 vmess 中的 address
                            "port": port,
                            "users": [
                                {
                                    "id": id,
                                    "alterId": int(matching_vmess.get('aid', 0)),  # 确保 alterId 是整数
                                    "email": matching_vmess.get('email', 't@t.tt'),
                                    "security": matching_vmess.get('scy', 'auto')
                                }
                            ]
                        }
                    ]
                },
                "streamSettings": {
                    "network": "ws",
                    "wsSettings": {
                        "path": matching_vmess.get('path', '/')
                    }
                },
                "mux": {
                    "enabled": False,
                    "concurrency": -1
                }
            }
            outbounds.append(outbound)

    config = {
        "log": {
            "access": "/tmp/vpn2.log",
            "error": "/tmp/vpn_err.log",
            "loglevel": "warning"
        },
        "inbounds": [
            {
                "tag": "socks",
                "port": 10808,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "sniffing": {
                    "enabled": True,
                    "destOverride": [
                        "http",
                        "tls"
                    ]
                },
                "settings": {
                    "auth": "noauth",
                    "udp": True,
                    "allowTransparent": False
                }
            },
            {
                "tag": "http",
                "port": 10809,
                "listen": "192.168.1.30",
                "protocol": "http",
                "sniffing": {
                    "enabled": True,
                    "destOverride": [
                        "http",
                        "tls"
                    ]
                },
                "settings": {
                    "auth": "noauth",
                    "udp": True,
                    "allowTransparent": False
                }
            }
        ],
        "outbounds": outbounds,
        "routing": {
            "domainStrategy": "IPIfNonMatch",
            "balancers": [
                {
                    "tag": "b1",
                    "selector": [outbound['tag'] for outbound in outbounds],
                    "retry": 3
                }
            ],
            "rules": [
                {
                    "type": "field",
                    "outboundTag": "direct",
                    "ip": ["geoip:private", "geoip:cn"]
                },
                {
                    "type": "field",
                    "outboundTag": "direct",
                    "domain": ["geosite:cn"]
                },
                {
                    "type": "field",
                    "network": "tcp,udp",
                    "balancerTag": "b1"
                }
            ]
        }
    }

    config_json = json.dumps(config, indent=4, ensure_ascii=False)
    print(config_json)
    
    if config_name:
        with open(config_name, 'w', encoding='utf-8') as f:
            f.write(config_json)
        print(f"Configuration saved to {config_name}")

def main():
    parser = argparse.ArgumentParser(description='Fetch and decode Base64 content from a URL.')
    parser.add_argument('url', type=str, help='The URL to fetch content from')
    parser.add_argument('--ps', type=str, nargs='*', help='List of ps values to match')
    parser.add_argument('--name', action='store_true', help='Print all ps values along with ip, port, and id')
    parser.add_argument('--config_name', type=str, help='The file name to save the generated configuration')
    args = parser.parse_args()
    
    fetch_and_decode(args.url, args.ps, args.name, args.config_name)

if __name__ == "__main__":
    main()
