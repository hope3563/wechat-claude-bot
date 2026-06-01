# 微信公众号 Claude 机器人

## 前置条件

1. **微信公众号**：已认证的服务号（订阅号部分功能受限）
2. **Anthropic API Key**：从 https://console.anthropic.com 获取
3. **云服务器**：有公网 IP 的服务器（或使用 Serverless）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 修改配置

编辑 `config.py`：

```python
WECHAT_TOKEN = "设置一个自定义的Token"  # 随意填写，与微信后台保持一致
ANTHROPIC_API_KEY = "sk-ant-xxx"        # 你的 Claude API Key
```

### 3. 本地测试

```bash
python app.py
```

服务将在 http://localhost:80 启动

### 4. 部署到服务器

```bash
# 使用 gunicorn 部署（生产环境）
gunicorn -w 4 -b 0.0.0.0:80 app:app
```

## 微信公众号配置

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入 **设置与开发** → **基本配置**
3. 填写服务器配置：
   - **URL**: `http://你的域名/wx`
   - **Token**: 与 `config.py` 中的 `WECHAT_TOKEN` 一致
   - **EncodingAESKey**: 点击随机生成
   - **消息加解密方式**: 明文模式（开发阶段）
4. 点击 **提交**，微信会验证你的服务器

## 功能说明

| 用户操作 | 说明 |
|----------|------|
| 发送任意消息 | 与 Claude AI 对话 |
| 发送「清除」/「clear」 | 重置对话历史 |
| 发送「帮助」 | 显示使用说明 |

## 注意事项

1. **对话上下文**：默认保留最近 10 轮对话（内存存储），生产环境建议用 Redis
2. **消息长度**：微信限制单条回复不超过 2000 字符
3. **响应时间**：微信要求 5 秒内响应，超时会重试。如 Claude 响应慢，可考虑异步处理
4. **并发限制**：Anthropic API 有并发限制，高流量时需做好限流

## 进阶优化

- [ ] 使用 Redis 存储对话历史
- [ ] 添加异步处理（Celery）
- [ ] 支持图片消息
- [ ] 添加用户白名单
- [ ] 接入日志系统
