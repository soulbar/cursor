# 订阅节点汇聚仓库

这是一个自动化的订阅节点汇聚和测速工具，用于收集、测试和管理多个订阅源的节点信息。

## 功能特性

1. **多源订阅汇聚**：自动从多个订阅链接获取节点信息
2. **智能测速**：自动测试节点延迟，过滤超过500ms的节点
3. **分流规则**：为YouTube、ChatGPT、Netflix、Cloudflare等网站配置分流规则
4. **自动更新**：每3小时自动更新节点信息
5. **Release发布**：自动在GitHub Release中生成可下载的YAML配置文件

## 订阅源

当前支持的订阅源：
- https://snip.soulbar.ggff.net/sub/204774c0-99c5-4454-bbd8-86775343a538
- https://boy.solobar.dpdns.org/soul/sub
- https://bfree.pages.dev/sub/normal/f5c17701-c7d6-4fe4-b8b9-70fdd5e20ace?app=clash
- https://solo-production-0eb5.up.railway.app/solo
- http://103.99.52.140:2096/sub/india

## 使用方法

### 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行脚本：
```bash
python main.py
```

### 自动更新

项目已配置GitHub Actions，会自动每3小时更新一次节点信息，并在Release中发布最新的配置文件。

## 配置文件

生成的Clash配置文件包含：
- 所有可用的节点（延迟<500ms）
- 分流规则：
  - YouTube
  - ChatGPT
  - Netflix
  - Cloudflare
  - Google服务
  - Telegram
  - 中国大陆网站（直连）

## 下载配置文件

在 [Releases](https://github.com/soulbar/cursor/releases) 页面下载最新的 `clash-config.yaml` 文件。

## 注意事项

- 测速功能需要网络连接
- 某些节点可能需要特殊处理
- 延迟测试使用TCP连接测试，可能因网络环境而异
