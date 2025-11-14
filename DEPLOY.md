# 部署说明

## GitHub仓库部署步骤

### 1. 创建GitHub仓库

1. 登录GitHub，点击右上角的"+"号，选择"New repository"
2. 填写仓库名称（例如：`clash-subscription-aggregator`）
3. 选择Public或Private
4. **不要**初始化README、.gitignore或license（我们已经创建了这些文件）
5. 点击"Create repository"

### 2. 推送代码到GitHub

在本地项目目录执行以下命令：

```bash
# 初始化Git仓库（如果还没有初始化）
git init

# 添加所有文件
git add .

# 提交代码
git commit -m "Initial commit: 订阅节点汇聚工具"

# 添加远程仓库（替换YOUR_USERNAME和YOUR_REPO为你的实际信息）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

### 3. 启用GitHub Actions

1. 进入仓库设置（Settings）
2. 点击左侧的"Actions" -> "General"
3. 确保"Workflow permissions"设置为"Read and write permissions"
4. 点击"Save"

### 4. 手动触发首次运行

1. 进入仓库的"Actions"标签页
2. 点击左侧的"自动更新订阅配置"工作流
3. 点击右上角的"Run workflow"按钮
4. 选择main分支，点击"Run workflow"

### 5. 检查运行结果

1. 在Actions页面查看工作流运行状态
2. 如果成功，会在"Releases"页面看到新的Release
3. 可以在Release中下载`clash-config.yaml`文件

## 本地测试

在推送到GitHub之前，可以在本地测试：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python main.py

# 检查生成的配置文件
cat clash-config.yaml
```

## 自定义配置

如果需要修改配置，编辑`config.py`文件：

- `SUBSCRIPTION_URLS`: 订阅链接列表
- `MAX_LATENCY`: 最大延迟阈值（毫秒）
- `RULES`: 分流规则配置

## 注意事项

1. 确保订阅链接可访问
2. 某些节点可能需要特殊配置
3. 测速结果可能因网络环境而异
4. GitHub Actions的免费额度有限，注意使用频率

## 故障排除

### GitHub Actions失败

1. 检查Actions日志，查看错误信息
2. 确保所有依赖都已安装
3. 检查订阅链接是否可访问

### 没有节点被获取

1. 检查订阅链接是否正确
2. 某些链接可能需要特殊处理（如Cloudflare保护）
3. 查看脚本输出的错误信息

### 配置文件格式错误

1. 确保生成的YAML格式正确
2. 检查Clash配置语法
3. 在Clash客户端中测试配置文件

