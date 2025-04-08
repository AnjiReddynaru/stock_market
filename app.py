import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
import json

# Streamlit Page Config
st.set_page_config(page_title="Gemini AI Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 Gemini AI Chatbot with Function Calling")

# Secure API Key Handling
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("Please set the Google API key in environment variables or Streamlit secrets!")
    st.stop()

# Initialize Gemini Client
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")  # Updated to a valid model

# System Instructions
SYSTEM_PROMPT = """
You are a specialized AI conversational assistant that can perform calculations and retrieve the current date and time using function calls.

Capabilities:
1. **Mathematical Calculations**: You can add, subtract, multiply, or divide numbers when requested.
   - Supported operations: `"add"`, `"subtract"`, `"multiply"`, `"divide"`.
   - You will return an error if division by zero is attempted or if invalid inputs are provided.
   - The function expects a JSON format: `{"operation": "add", "numbers": [4, 5, 6]}`.

2. **Fetching the Current Time**: You can provide the current date and time in `"YYYY-MM-DD HH:MM:SS"` format.
3. **Giving back Previous Messages**: You can provide the previous messages in the chat history which happened in thes conversation.
Rules:
- If the user asks for any **calculation**, invoke the `calculate` function.
- If the user asks for the **current time**, invoke the `get_time` function.
- If the user asks for the previous messages, give the user, the previous respective messages.
- If the user's question is unrelated to calculations or time, inform them that you can only perform these tasks.

When you need to call a function, respond in the following format:

**For calculations:**
[CALL:calculate] {"operation": "add", "numbers": [10, 20, 30]}
**For getting the time:**
[CALL:get_time]


Do **not** answer queries unrelated to calculations or time or previous messages.

"""

# Tool Functions
def get_time():
    """Returns the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(operation, numbers):
    """Performs basic calculations on a list of numbers."""
    if not isinstance(numbers, list) or len(numbers) < 2:
        return "Error: Provide at least two numbers."

    try:
        if operation == "add":
            return sum(numbers)
        elif operation == "subtract":
            return numbers[0] - sum(numbers[1:])
        elif operation == "multiply":
            result = 1
            for num in numbers:
                result *= num
            return result
        elif operation == "divide":
            result = numbers[0]
            for num in numbers[1:]:
                if num == 0:
                    return "Error: Division by zero is not allowed."
                result /= num
            return result
        else:
            return "Error: Unsupported operation. Use 'add', 'subtract', 'multiply', or 'divide'."
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit Chat Sessiona
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you today?"}]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle User Input
user_input = st.chat_input("Ask me anything...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Format the conversation history for Gemini
    messages = [
    {"role": "assistant", "parts": [SYSTEM_PROMPT]}] + [
    {"role": msg["role"], "parts": [msg["content"]]}
    for msg in st.session_state.messages
    ]


    # Call Gemini API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # response = model.generate_content(SYSTEM_PROMPT + "\nUser: " + user_input)
            response = model.generate_content(messages)  # Pass the structured conversation

            assistant_reply = response.text.strip()

            # Check if response requests a tool execution
            # Check if AI wants to invoke a tool
            if assistant_reply.startswith("[CALL:get_time]"):
                tool_result = get_time()
                assistant_reply = tool_result

            elif assistant_reply.startswith("[CALL:calculate]"):
                try:
                    json_data = assistant_reply[len("[CALL:calculate]"):].strip()
                    params = json.loads(json_data)
                    tool_result = calculate(params.get("operation"), params.get("numbers"))
                    assistant_reply = str(tool_result)
                except Exception as e:
                    assistant_reply = f"Error processing calculation request: {str(e)}"


            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            st.markdown(assistant_reply)
