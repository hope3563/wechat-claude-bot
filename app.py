import hashlib
import os
import time
from flask import Flask, request, make_response
import anthropic

app = Flask(__name__)

# 从环境变量读取配置
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.xiaomimimo.com/anthropic")
MIMO_MODEL = os.environ.get("MIMO_MODEL", "mimo-7b")
WECHAT_TOKEN = os.environ.get("WECHAT_TOKEN", "")

# Claude 客户端（指向 MIMO API）
client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY,
    base_url=ANTHROPIC_BASE_URL
)

# 对话历史存储（生产环境建议用 Redis）
conversation_history = {}


def verify_signature(signature, timestamp, nonce):
    """验证微信签名"""
    params = sorted([WECHAT_TOKEN, timestamp, nonce])
    hash_str = hashlib.sha1("".join(params).encode()).hexdigest()
    return hash_str == signature


def parse_message(xml_data):
    """解析微信 XML 消息"""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_data)
    msg = {}
    for child in root:
        msg[child.tag] = child.text
    return msg


def build_reply(to_user, from_user, content):
    """构建回复 XML"""
    return f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""


def get_ai_response(user_id, user_message):
    """调用 MIMO API 获取回复"""
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })

    # 只保留最近 20 条消息
    messages = conversation_history[user_id][-20:]

    try:
        response = client.messages.create(
            model=MIMO_MODEL,
            max_tokens=1024,
            system="你是一个友善的 AI 助手，通过微信公众号与用户交流。请简洁回答问题。",
            messages=messages
        )
        reply = response.content[0].text

        conversation_history[user_id].append({
            "role": "assistant",
            "content": reply
        })

        return reply
    except Exception as e:
        print(f"AI API Error: {e}")
        return "抱歉，AI 暂时无法回复，请稍后再试。"


@app.route("/wx", methods=["GET", "POST"])
def wechat():
    """微信接口入口"""
    if request.method == "GET":
        signature = request.args.get("signature", "")
        timestamp = request.args.get("timestamp", "")
        nonce = request.args.get("nonce", "")
        echostr = request.args.get("echostr", "")

        if verify_signature(signature, timestamp, nonce):
            return echostr
        return "Verification failed"

    else:
        try:
            msg = parse_message(request.data)
            user_id = msg.get("FromUserName", "")
            content = msg.get("Content", "").strip()

            if not content:
                return "success"

            if content.lower() in ["clear", "清除", "重置"]:
                conversation_history.pop(user_id, None)
                reply = "对话已重置，可以开始新的对话了！"
            elif content == "帮助":
                reply = """【使用说明】
• 直接发消息即可与 AI 对话
• 发送「清除」重置对话历史
• 发送「帮助】查看此说明"""
            else:
                reply = get_ai_response(user_id, content)

            if len(reply) > 2000:
                reply = reply[:1997] + "..."

            response = make_response(build_reply(
                to_user=user_id,
                from_user=msg.get("ToUserName", ""),
                content=reply
            ))
            response.content_type = "application/xml"
            return response

        except Exception as e:
            print(f"Error: {e}")
            return "success"


@app.route("/")
def health():
    return "WeChat Claude Bot is running!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port, debug=False)
