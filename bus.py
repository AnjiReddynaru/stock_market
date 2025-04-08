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
To provide users with real-time bus arrival information, integrating APSRTC's live tracking features into your chatbot is essential. Here are the methods available:

**1. APSRTC Live Track Application:**

APSRTC offers a mobile application that provides real-time updates on bus locations and arrival times. Key features include:

- **Real-Time Updates:** View current locations and expected arrival times of buses at your stop or destination.
- **Active Planner:** Access updated bus services and route information between two stops to plan your travel effectively.
- **Favorites:** Add frequent routes to your favorites for quick tracking.
- **Offline Mode:** View bus schedules even without internet connectivity.
- **Emergency Alerts:** Report accidents or bus breakdowns to APSRTC Helpline and seek assistance.
- **Auto Refresh:** The app automatically refreshes data for the latest information.

The APSRTC Live Track app is available for both Android and iOS devices. citeturn0search6turn0search3

**2. SMS Service for Bus Tracking:**

For users without smartphones or those preferring not to use the app, APSRTC provides an SMS service to track buses:

- **How It Works:**
  - Send an SMS with the bus service number to 9246022333.
  - Receive a return SMS with the time details of the previous stop and the expected time of arrival (ETA) at the next stop.

- **Example:**
  - To track bus service number 5538, send: `RTC 5538`
  - You will receive information about the bus's current location and estimated arrival times.

This service allows passengers to obtain live tracking information without the need for a smartphone application. citeturn0search4

**3. Integration into Your Chatbot:**

To incorporate these features into your chatbot:

- **APSRTC Live Track API:** Utilize APSRTC's official API (if available) to access real-time bus tracking data. This will enable your chatbot to provide users with current bus locations and arrival times.
- **SMS Integration:** Implement functionality in your chatbot to send SMS requests to APSRTC's tracking service and relay the responses to users. This ensures users can receive live tracking information directly through the chatbot.

By integrating these methods, your chatbot can deliver accurate and timely bus arrival information, enhancing the travel experience for users in Andhra Pradesh. 
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
