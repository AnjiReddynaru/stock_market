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
To develop a chatbot that provides news and addresses sensitive issues for a specific college in Andhra Pradesh, you can design prompts that guide users to input the college's name. Upon receiving the college name, the chatbot can retrieve and present relevant news articles and information related to that institution. Here's an example of how you might structure such prompts:

**User Prompt:**
"Please enter the name of the college you're interested in to receive the latest news and updates."

**User Input:**
[User enters the college name, e.g., "Andhra University"]

**Chatbot Response:**
"Here are the latest news and updates for Andhra University:"

- **News Article 1:** *Title:* 'Andhra University Hosts Annual Science Symposium'
  - *Summary:* Highlights from the recent symposium focusing on advancements in renewable energy.
  - *Date:* March 15, 2025
  - *Source:* [The Hindu](https://www.thehindu.com/news/national/andhra-pradesh/article12345678.ece)

- **News Article 2:** *Title:* 'Student Welfare Initiatives at Andhra University'
  - *Summary:* An overview of new support programs introduced for student well-being.
  - *Date:* April 1, 2025
  - *Source:* [Times of India](https://timesofindia.indiatimes.com/topic/andhra-university/news)

- **Sensitive Issue Report:** *Title:* 'Investigation into Alleged Misconduct at Andhra University Hostel'
  - *Summary:* Details of the ongoing investigation into reported incidents within the university hostel.
  - *Date:* April 5, 2025
  - *Source:* [NDTV](https://www.ndtv.com/andhra-pradesh-news/investigation-andhra-university-hostel-misconduct-254933)

**Development Considerations:**

- **Data Sources:** Integrate the chatbot with reliable news APIs or RSS feeds that provide updates on Andhra Pradesh colleges. Ensure that the sources are reputable and regularly updated.

- **Sensitive Information Handling:** For sensitive matters, implement features that allow users to report issues confidentially. Provide resources or contact information for appropriate support services.

- **User Interaction:** Allow users to specify the type of information they're interested in (e.g., academic news, events, administrative updates) to personalize their experience.

- **Privacy and Security:** Ensure that the chatbot complies with data protection regulations, especially when handling personal or sensitive information.

By implementing these features, your chatbot can effectively serve users seeking information about specific colleges in Andhra Pradesh, delivering timely news and addressing sensitive issues appropriately. 

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