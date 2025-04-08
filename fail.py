
import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
import json

# Streamlit Page Config
st.set_page_config(page_title="Gemini AI Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 chatbot fot detecting the failures in chatbot ")

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
To construct a chatbot capable of effectively analyzing and understanding its own failures, it's essential to design it with self-awareness and robust error-handling mechanisms. Below is a comprehensive prompt to guide the development of such a chatbot:

**Chatbot Development Prompt: Self-Aware Error Analysis and Handling**

1. **Objective:**
   - Develop a chatbot that can autonomously recognize, analyze, and learn from its failures to enhance user interactions and overall performance.

2. **Core Features:**

   - **Failure Detection:**
     - Implement mechanisms to identify when the chatbot's responses are inadequate, such as misunderstanding user intents, providing irrelevant information, or failing to handle complex queries.

   - **Error Logging:**
     - Maintain detailed logs of interactions where failures occur, capturing user inputs, chatbot responses, and contextual information for analysis.

   - **Self-Analysis Module:**
     - Develop algorithms that analyze error logs to identify patterns and root causes of failures, such as limitations in training data, model architecture, or conversational design.

   - **Adaptive Learning:**
     - Enable the chatbot to update its knowledge base and refine its response generation algorithms based on insights gained from failure analyses, ensuring continuous improvement.

   - **User Feedback Integration:**
     - Incorporate mechanisms for users to provide feedback on chatbot responses, using this data to further inform the self-analysis and learning processes.

3. **Error Handling Strategies:**

   - **Clear Communication:**
     - Design the chatbot to acknowledge when it doesn't understand a user's query, using friendly and non-blaming language. For example:
       - "I'm sorry, I didn't quite catch that. Could you please rephrase your question?"

   - **Fallback Options:**
     - Provide users with alternative ways to obtain assistance when the chatbot cannot fulfill a request, such as:
       - "I apologize, but I'm unable to assist with that. Would you like to speak with a human representative?"

   - **Continuous Improvement Loop:**
     - Regularly update the chatbot's training data and algorithms based on ongoing analyses of failures and user feedback, fostering a cycle of continuous enhancement.

4. **Performance Monitoring:**

   - **Analytics Dashboard:**
     - Develop a dashboard to monitor key performance indicators (KPIs) such as response accuracy, user satisfaction ratings, and frequency of failures, enabling data-driven decision-making.

   - **Regular Audits:**
     - Schedule periodic evaluations of the chatbot's performance to identify areas needing improvement and to ensure alignment with user expectations and business objectives.

5. **User Experience Considerations:**

   - **Personalization:**
     - Equip the chatbot with the ability to remember user preferences and past interactions, tailoring responses to individual users for a more engaging experience.

   - **Transparency:**
     - Clearly communicate the chatbot's capabilities and limitations to users, setting realistic expectations and building trust. For instance:
       - "I'm an AI assistant trained to help with common questions. For more complex issues, I can connect you with a human expert."

By implementing these features and strategies, you can develop a chatbot that not only recognizes and learns from its failures but also provides users with a seamless and satisfying interaction experience. 
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