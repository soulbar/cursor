# 订阅链接配置
SUBSCRIPTION_URLS = [
    "https://snip.soulbar.ggff.net/sub/204774c0-99c5-4454-bbd8-86775343a538",
    "https://boy.solobar.dpdns.org/soul/sub",
    "https://bfree.pages.dev/sub/normal/f5c17701-c7d6-4fe4-b8b9-70fdd5e20ace?app=clash",
    "https://solo-production-0eb5.up.railway.app/solo",
    "http://103.99.52.140:2096/sub/india"
]

# 测速配置
MAX_LATENCY = 500  # 最大延迟（毫秒），超过此值的节点将被过滤
TEST_TIMEOUT = 5  # 测速超时时间（秒）

# 分流规则配置
RULES = {
    "YouTube": [
        "DOMAIN-SUFFIX,youtube.com",
        "DOMAIN-SUFFIX,googlevideo.com",
        "DOMAIN-SUFFIX,youtube-nocookie.com",
        "DOMAIN-SUFFIX,ytimg.com",
        "DOMAIN-SUFFIX,youtu.be"
    ],
    "ChatGPT": [
        "DOMAIN-SUFFIX,openai.com",
        "DOMAIN-SUFFIX,chatgpt.com",
        "DOMAIN-SUFFIX,anthropic.com",
        "DOMAIN-SUFFIX,claude.ai",
        "DOMAIN-SUFFIX,openai.org",
        "DOMAIN-SUFFIX,oaistatic.com"
    ],
    "Netflix": [
        "DOMAIN-SUFFIX,netflix.com",
        "DOMAIN-SUFFIX,nflxext.com",
        "DOMAIN-SUFFIX,nflximg.com",
        "DOMAIN-SUFFIX,nflxso.net",
        "DOMAIN-SUFFIX,nflxvideo.net"
    ],
    "Cloudflare": [
        "DOMAIN-SUFFIX,cloudflare.com",
        "DOMAIN-SUFFIX,cloudflare.net",
        "DOMAIN-SUFFIX,cloudflare-dns.com",
        "IP-CIDR,1.1.1.0/24",
        "IP-CIDR,1.0.0.0/24"
    ],
    "Google": [
        "DOMAIN-SUFFIX,google.com",
        "DOMAIN-SUFFIX,googleapis.com",
        "DOMAIN-SUFFIX,gstatic.com",
        "DOMAIN-SUFFIX,googleusercontent.com",
        "DOMAIN-SUFFIX,gmail.com",
        "DOMAIN-SUFFIX,googlemail.com"
    ],
    "Telegram": [
        "DOMAIN-SUFFIX,telegram.org",
        "DOMAIN-SUFFIX,tdesktop.com",
        "DOMAIN-SUFFIX,telegra.ph",
        "IP-CIDR,91.108.56.0/22",
        "IP-CIDR,91.108.4.0/22",
        "IP-CIDR,91.108.8.0/22",
        "IP-CIDR,91.108.12.0/22",
        "IP-CIDR,91.108.16.0/22",
        "IP-CIDR,91.108.20.0/22",
        "IP-CIDR,149.154.160.0/20",
        "IP-CIDR,205.172.60.0/22"
    ],
    "Twitter": [
        "DOMAIN-SUFFIX,twitter.com",
        "DOMAIN-SUFFIX,twimg.com",
        "DOMAIN-SUFFIX,t.co",
        "DOMAIN-SUFFIX,x.com"
    ],
    "Facebook": [
        "DOMAIN-SUFFIX,facebook.com",
        "DOMAIN-SUFFIX,fb.com",
        "DOMAIN-SUFFIX,instagram.com",
        "DOMAIN-SUFFIX,whatsapp.com"
    ],
    "GitHub": [
        "DOMAIN-SUFFIX,github.com",
        "DOMAIN-SUFFIX,githubusercontent.com",
        "DOMAIN-SUFFIX,github.io"
    ],
    "Microsoft": [
        "DOMAIN-SUFFIX,microsoft.com",
        "DOMAIN-SUFFIX,office.com",
        "DOMAIN-SUFFIX,office365.com",
        "DOMAIN-SUFFIX,onedrive.com",
        "DOMAIN-SUFFIX,outlook.com",
        "DOMAIN-SUFFIX,hotmail.com"
    ]
}

# Clash配置模板
CLASH_CONFIG_TEMPLATE = {
    "port": 7890,
    "socks-port": 7891,
    "allow-lan": False,
    "mode": "rule",
    "log-level": "info",
    "external-controller": "127.0.0.1:9090",
    "dns": {
        "enable": True,
        "listen": "0.0.0.0:53",
        "enhanced-mode": "fake-ip",
        "fake-ip-range": "198.18.0.1/16",
        "nameserver": [
            "223.5.5.5",
            "119.29.29.29",
            "1.1.1.1",
            "8.8.8.8"
        ],
        "fallback": [
            "1.1.1.1",
            "8.8.8.8",
            "tls://dns.cloudflare.com:853",
            "tls://dns.google:853"
        ],
        "fallback-filter": {
            "geoip": True,
            "ipcidr": [
                "240.0.0.0/4"
            ]
        }
    }
}

