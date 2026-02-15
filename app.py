import streamlit as st
import requests
from dotenv import load_dotenv
import os
import time
import json

# Load API key from .env
if "OPENROUTER_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
elif:
    load_dotenv()
    API_KEY = os.getenv("OPENROUTER_API_KEY")
else:
    API_KEY ="s5k-or-v1-3f45082256522b517957798bd7ba0a5683bf98e527b5066bc6c24e099185621"

st.set_page_config(
    page_title="AI Chat Assistant", 
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stButton button {
        width: 100%;
    }
    .error-message {
        color: #d32f2f;
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .model-info {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "model" not in st.session_state:
    st.session_state.model = "openai/gpt-3.5-turbo"

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Settings")
    
    # API Key status
    if API_KEY:
        st.success("✅ API Key Loaded")
        # Show first few characters of API key for verification
    else:
        st.error("❌ API Key Missing! Add it to .env file")
        st.code("OPENROUTER_API_KEY=your_key_here")
    
    st.divider()
    
     
    # Statistics
    st.metric("Total Messages", len(st.session_state.messages))
    st.metric("Total Tokens", st.session_state.total_tokens)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

# Main chat area
st.title("🤖 AI Chat Assistant")
st.caption("Chat with multiple AI models through OpenRouter")

# Check for API key first
if not API_KEY:
    st.error("""
    ### 🔑 API Key Not Found!
    
    Please add your OpenRouter API key to the `.env` file:
    
    ```
    OPENROUTER_API_KEY=your_api_key_here
    ```
    
    **Don't have an API key?** Get one at [OpenRouter.ai](https://openrouter.ai)
    """)
    st.stop()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and "tokens" in message:
            st.caption(f"⚡ Tokens: {message['tokens']}")

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Prepare conversation history (last 5 messages for context)
    messages_for_api = []
    for msg in st.session_state.messages[-5:]:
        messages_for_api.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Get AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Show thinking indicator
            with st.spinner("🤔 Thinking..."):
                
                # Prepare headers - FIXED AUTHENTICATION
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8501",  # Required by OpenRouter
                    "X-Title": "AI Chat Assistant"  # Required by OpenRouter
                }
                
                # Prepare request data
                data = {
                    "model": st.session_state.model,
                    "messages": messages_for_api,
                    
                }
                
                # Make API request with timeout
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                # Check response status
                if response.status_code == 401:
                    st.error("""
                    ### 🔒 Authentication Failed
                    
                    Your API key is invalid or expired. Please check:
                    1. The key is correct in your `.env` file
                    2. Your OpenRouter account is active
                    3. Try generating a new key at [OpenRouter Keys](https://openrouter.ai/keys)
                    """)
                    st.stop()
                    
                elif response.status_code == 402:
                    st.error("""
                    ### 💳 Payment Required
                    
                    Your OpenRouter account needs credits. Add funds at [OpenRouter](https://openrouter.ai)
                    """)
                    st.stop()
                    
                elif response.status_code == 429:
                    st.error("### ⏳ Rate Limit Exceeded\n\nPlease wait a moment before sending more messages.")
                    st.stop()
                    
                elif response.status_code != 200:
                    st.error(f"### Error {response.status_code}\n\n{response.text}")
                    st.stop()
                
                # Parse response
                response_data = response.json()
                
                # Extract reply
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    reply = response_data['choices'][0]['message']['content']
                    
                    # Get token usage
                    tokens_used = response_data.get('usage', {}).get('total_tokens', 0)
                    st.session_state.total_tokens += tokens_used
                    
                    # Display response with typing effect
                    displayed_text = ""
                    for char in reply:
                        displayed_text += char
                        message_placeholder.write(displayed_text + "▌")
                        time.sleep(0.003)
                    
                    # Final message
                    message_placeholder.write(reply)
                    
                    # Save to session
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": reply,
                        "tokens": tokens_used
                    })
                    
                else:
                    st.error("Unexpected API response format")
                    st.json(response_data)
                    
        except requests.exceptions.Timeout:
            st.error("⏰ Request timeout! Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Connection error! Please check your internet.")
        except json.JSONDecodeError:
            st.error("❌ Invalid response from API")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Footer with helpful info
st.divider()
with st.expander("ℹ️ Help & Information"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Free Models Available:**")
        st.markdown("- Meta Llama 2 70B")
        st.markdown("- Mistral 7B")
        st.markdown("- OpenRouter Auto")
    
    with col2:
        st.markdown("**Need Help?**")
        st.markdown("- [OpenRouter Documentation](https://openrouter.ai/docs)")
        st.markdown("- [Get API Key](https://openrouter.ai/keys)")

        st.markdown("- [Add Credits](https://openrouter.ai/settings)")


