import streamlit as st
import requests
import json

# 设置页面配置
st.set_page_config(page_title="AI聊天助手", page_icon="🤖", layout="wide")

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_configured' not in st.session_state:
    st.session_state.api_configured = False

# 侧边栏配置
with st.sidebar:
    st.title("API配置")
    
    api_provider = st.selectbox(
        "选择API提供商",
        ["OpenAI", "Anthropic Claude", "其他"]
    )
    
    api_key = st.text_input("API密钥", type="password")
    
    if api_provider == "其他":
        api_endpoint = st.text_input("API端点URL")
        model_name = st.text_input("模型名称")
    elif api_provider == "OpenAI":
        api_endpoint = "https://api.openai.com/v1/chat/completions"
        model_name = st.selectbox("选择模型", ["gpt-3.5-turbo", "gpt-4"])
    elif api_provider == "Anthropic Claude":
        api_endpoint = "https://api.anthropic.com/v1/messages"
        model_name = st.selectbox("选择模型", ["claude-3-opus-20240229", "claude-3-sonnet-20240229"])
    
    if st.button("保存配置"):
        if api_key:
            st.session_state.api_key = api_key
            st.session_state.api_endpoint = api_endpoint
            st.session_state.model_name = model_name
            st.session_state.api_provider = api_provider
            st.session_state.api_configured = True
            st.success("API配置成功！")
        else:
            st.error("请输入API密钥")

# 主聊天界面
st.title("AI聊天助手 🤖")

if not st.session_state.api_configured:
    st.warning("请先在侧边栏配置API信息")
else:
    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("输入你的消息..."):
        # 添加用户消息到历史
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 调用API获取回复
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            try:
                if st.session_state.api_provider == "OpenAI":
                    headers = {
                        "Authorization": f"Bearer {st.session_state.api_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": st.session_state.model_name,
                        "messages": st.session_state.messages,
                        "temperature": 0.7
                    }
                    response = requests.post(
                        st.session_state.api_endpoint,
                        headers=headers,
                        json=data
                    )
                    response.raise_for_status()
                    assistant_message = response.json()['choices'][0]['message']['content']
                
                elif st.session_state.api_provider == "Anthropic Claude":
                    headers = {
                        "x-api-key": st.session_state.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                    # 转换消息格式为Claude API格式
                    claude_messages = []
                    for msg in st.session_state.messages:
                        claude_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                    
                    data = {
                        "model": st.session_state.model_name,
                        "messages": claude_messages,
                        "max_tokens": 1000
                    }
                    response = requests.post(
                        st.session_state.api_endpoint,
                        headers=headers,
                        json=data
                    )
                    response.raise_for_status()
                    assistant_message = response.json()['content'][0]['text']
                
                else:
                    # 通用API调用（需要根据具体API调整）
                    headers = {
                        "Authorization": f"Bearer {st.session_state.api_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": st.session_state.model_name,
                        "messages": st.session_state.messages
                    }
                    response = requests.post(
                        st.session_state.api_endpoint,
                        headers=headers,
                        json=data
                    )
                    response.raise_for_status()
                    assistant_message = response.json()['choices'][0]['message']['content']
                
                message_placeholder.markdown(assistant_message)
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                
            except requests.exceptions.RequestException as e:
                st.error(f"API调用失败: {str(e)}")
            except KeyError as e:
                st.error(f"响应格式错误: {str(e)}")
            except Exception as e:
                st.error(f"发生错误: {str(e)}")

# 清除聊天历史按钮
if st.button("清除聊天历史"):
    st.session_state.messages = []
    st.rerun()